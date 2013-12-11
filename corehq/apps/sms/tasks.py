from datetime import datetime, timedelta
from celery.task import task
from time import sleep
from redis_cache.cache import RedisCache
from corehq.apps.sms.models import SMSLog, OUTGOING, INCOMING
from corehq.apps.sms.api import send_message_via_backend, process_incoming
from django.conf import settings
from corehq.apps.domain.models import Domain

from dimagi.utils.couch.cache import cache_core
rcache = cache_core.get_redis_default_cache()

# 5-minute lock timeout
LOCK_TIMEOUT = 5

# 5-minute wait to reprocess an unsuccessful attempt
REPROCESS_INTERVAL = 5

# Max number of attempts before giving up on processing an SMS
MAX_PROCESSING_ATTEMPTS = 3

# Number of minutes to wait before retrying SMS that was delayed because the
# domain restricts sending SMS to certain days/times.
DOMAIN_RESTRICTED_RETRY_INTERVAL = 15

def set_error(msg):
    msg.error = True
    msg.save()

def handle_unsuccessful_processing_attempt(msg):
    msg.num_processing_attempts += 1
    if msg.num_processing_attempts < MAX_PROCESSING_ATTEMPTS:
        delay_processing(msg, REPROCESS_INTERVAL)
    else:
        set_error(msg)

def handle_successful_processing_attempt(msg):
    msg.num_processing_attempts += 1
    msg.processed = True
    msg.save()

def delay_processing(msg, minutes):
    msg.datetime_to_process += timedelta(minutes=minutes)
    msg.save()

def get_lock(client, key):
    return client.lock(key, timeout=LOCK_TIMEOUT*60)

def time_within_windows(utcnow, windows):
    weekday = utcnow.weekday()
    time = utcnow().time()

    for window in windows:
        if (weekday == window.day and
            time >= window.start_time and
            time <= window.end_time):
            return True

    return False

def handle_domain_specific_delays(msg, domain_object, utcnow):
    """
    Checks whether or not we need to hold off on sending an outbound message
    due to any restrictions set on the domain, and delays processing of the
    message if necessary.

    Returns True if a delay was made, False if not.
    """
    if msg.direction != OUTGOING:
        return False

    if len(domain_object.restricted_sms_times) > 0:
        if time_within_windows(utcnow, domain_object.restricted_sms_times):
            delay_processing(msg, DOMAIN_RESTRICTED_RETRY_INTERVAL)
            return True

    if len(domain_object.sms_conversation_times) > 0:
        if time_within_windows(utcnow, domain_object.sms_conversation_times):
            conversation_start_timestamp = utcnow - timedelta(minutes=sms_conversation_length)
            if SMSLog.inbound_entry_exists(msg.couch_recipient_doc_type,
                                           msg.couch_recipient,
                                           conversation_start_timestamp,
                                           utcnow):
                delay_processing(msg, 1)
                return True

    return False

def handle_outgoing(msg):
    if send_message_via_backend(msg):
        handle_successful_processing_attempt(msg)
    else:
        handle_unsuccessful_processing_attempt(msg)

def handle_incoming(msg):
    try:
        process_incoming(msg)
        handle_successful_processing_attempt(msg)
    except:
        handle_unsuccessful_processing_attempt(msg)

@task(queue="sms_queue")
def process_sms(message_id):
    """
    message_id - _id of an SMSLog entry
    """
    if not isinstance(rcache, RedisCache):
        return
    try:
        client = rcache.raw_client
    except NotImplementedError:
        return

    utcnow = datetime.utcnow()
    message_lock = get_lock(client, "sms-queue-processing-%s" % message_id)

    if message_lock.acquire(blocking=False):
        msg = SMSLog.get(message_id)

        domain_object = Domain.get_by_name(msg.domain, strict=True)
        if handle_domain_specific_delays(msg, domain_object):
            message_lock.release()
            return

        if not msg.processed and msg.datetime_to_process < utcnow:
            recipient_lock = get_lock(client, "sms-queue-recipient-%s" % msg.couch_recipient)
            recipient_lock.acquire(blocking=True)

            if msg.direction == OUTGOING:
                handle_outgoing(msg)
            elif msg.direction == INCOMING:
                handle_incoming(msg)
            else:
                set_error(msg)

            recipient_lock.release()
        message_lock.release()

