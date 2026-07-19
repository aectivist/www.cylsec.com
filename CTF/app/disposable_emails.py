"""Blocklist of known disposable/throwaway email providers."""

DISPOSABLE_EMAIL_DOMAINS = frozenset({
    'mailinator.com', 'mailinator.net', 'mailinator.org', 'mailinator2.com',
    'guerrillamail.com', 'guerrillamail.net', 'guerrillamail.org', 'guerrillamail.biz',
    'guerrillamail.de', 'guerrillamailblock.com', 'sharklasers.com', 'grr.la',
    'pokemail.net', 'spam4.me',
    '10minutemail.com', '10minutemail.net', '10minutemail.co.uk', '20minutemail.com',
    'temp-mail.org', 'tempmail.com', 'tempmail.net', 'tempmail.ninja', 'tempmailo.com',
    'tempail.com', 'tempmailaddress.com', 'tmpmail.org', 'tmpmail.net',
    'throwawaymail.com', 'throwaway.email', 'trashmail.com', 'trashmail.net',
    'trashmail.me', 'trash-mail.com', 'wegwerfmail.de', 'wegwerfmail.net',
    'yopmail.com', 'yopmail.net', 'yopmail.fr', 'cool.fr.nf', 'jetable.fr.nf',
    'dispostable.com', 'fakeinbox.com', 'fakemailgenerator.com', 'getnada.com',
    'maildrop.cc', 'mailnesia.com', 'mailcatch.com', 'mailsac.com', 'mintemail.com',
    'mohmal.com', 'moakt.com', 'moakt.cc', 'emailondeck.com', 'spamgourmet.com',
    'anonaddy.com', 'burnermail.io', 'discard.email', 'discardmail.com',
    'mytemp.email', 'nada.email', 'notsharingmy.info', 'inboxbear.com',
    'crazymailing.com', 'harakirimail.com', 'incognitomail.com', 'mailexpire.com',
    'mailnull.com', 'meltmail.com', 'spambog.com', 'spamfree24.org', 'spamavert.com',
    'trbvm.com', 'boximail.com', 'deadaddress.com', 'mailmetrash.com',
    'tempinbox.com', 'e4ward.com', 'fake-mail.net', 'fastmail.pro',
    'getairmail.com', 'guerillamail.info', 'inboxkitten.com', 'luxusmail.org',
    'no-spam.ws', 'nowmymail.com', 'onewaymail.com', 'sofimail.com',
    'spamherelots.com', 'superrito.com', 'tempemail.co', 'tempmailer.com',
    'tempr.email', 'zippymail.info', 'objectmail.com', '33mail.com',
    'temp-inbox.com', 'temporarymail.com', 'emailtemporario.com.br',
    'einrot.com', 'kurzepost.de', 'mail-temporaire.fr', 'correotemporal.org',
})


def is_disposable_email(email):
    if not email or '@' not in email:
        return False
    domain = email.rsplit('@', 1)[-1].strip().lower()
    return domain in DISPOSABLE_EMAIL_DOMAINS
