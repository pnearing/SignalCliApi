#!/usr/bin/env python3

import argparse

from signalAccount import Account
from signalAttachment import Attachment
from signalCli import SignalCli
from signalMention import Mention
from signalMentions import Mentions
from signalPreview import Preview
from signalReceivedMessage import ReceivedMessage
from signalReaction import Reaction
from signalReceipt import Receipt
from signalSentMessage import SentMessage
from signalSyncMessage import SyncMessage
from signalTypingMessage import TypingMessage


def all_msg_cb(account: Account, message: ReceivedMessage | Receipt | TypingMessage | SyncMessage):
    print("ALL")
    # print(message)
    return


def received_msg_cb(account: Account, message: ReceivedMessage):
    print("RECEIVED")
    # message.mark_read()
    print(message)
    print("Received message FROM: %s AT: %s on DEVICE: %s" % (
        message.sender.get_display_name(),
        message.timestamp.get_display_time(),
        message.device.get_display_name(),
    ))
    if message.recipient_type == 'group':
        print("In GROUP: %s" % message.recipient.get_display_name())
    if message.quote is not None:
        if message.quote.attachments is not None:
            for attachment in message.quote.attachments:
                displayName = "<UNKNOWN-ATTACHMENT>"
                if attachment.file_name is not None and attachment.file_name != '':
                    displayName = attachment.file_name
                elif attachment.local_path is not None and attachment.exists:
                    displayName = attachment.local_path
                elif attachment.thumbnail is not None and attachment.thumbnail.exists:
                    displayName = "Thumbnail: %s" % attachment.thumbnail.local_path
                print("Trying to display attachment: %s...\n    Success=" % displayName, end='', flush=True)
                # returnValue = attachment.display()
                # print(returnValue)

        quoted_message = account.messages.get_quoted(message.quote)
        if quoted_message is None:
            print("Quoting a message not found in history.")
        else:
            if isinstance(quoted_message, ReceivedMessage):
                print("Quoting received message FROM:%s AT: %s" % (quoted_message.sender.get_display_name(),
                                                                   quoted_message.timestamp.get_display_time()))
                if quoted_message.recipient_type == 'group':
                    print("in GROUP: %s" % quoted_message.recipient.get_display_name())
            elif isinstance(quoted_message, SentMessage):
                print("Quoting message sent AT: %s" % quoted_message.timestamp.get_display_time())
                if quoted_message.recipient_type == 'group':
                    print("In GROUP: %s" % quoted_message.recipient.get_display_name())
        quoted_text = message.quote.parse_mentions()
        print("Quoted TEXT: %s" % quoted_text)

    print("--------Begin Message--------")
    display_text = message.parse_mentions()
    print(display_text)
    print("---------End Message---------")

    if message.attachments is not None:
        for attachment in message.attachments:
            displayName = "<UNKNOWN-ATTACHMENT>"
            if attachment.file_name is not None and attachment.file_name != '':
                displayName = attachment.file_name
            elif attachment.local_path is not None and attachment.exists:
                displayName = attachment.local_path
            elif attachment.thumbnail is not None and attachment.thumbnail.exists:
                displayName = "Thumbnail: %s" % attachment.thumbnail.local_path
            print("Trying to display attachment: %s...\n    Success=" % displayName, end='', flush=True)
            # returnValue = attachment.display()
            # print(returnValue)

    # message.react('😀')#👍👎
    # if (message.hasQuote == True):
    #     print("In reply to:")
    #     if (message.quote != None):
    #         print(message.quote.timestamp)
    #     else:
    #         print("A message not in history")
    return


def receipt_msg_cb(account, message: Receipt):
    print("RECEIPT")
    print(message.body)
    return


def sync_msg_cb(account, message):
    print("SYNC")
    print(message)
    return


def type_msg_cb(account, message: TypingMessage):
    print("TYPING")
    print(message.body)
    return


def story_msg_cb(account, message):
    print("STORY")
    print(message)
    return


def payment_msg_cb(account, message):
    print("PAYMENT")
    print(message)
    return


def reaction_msg_cb(account, message: Reaction):
    print("REACTION")
    print(message.body)
    return


def call_msg_cb(account, message):
    print("CALL")
    print(message)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Signal test code.")
    parser.add_argument("--register", help="--register NUMBER, number to register.")
    parser.add_argument("--captcha",
                        help="--captcha CAPTCHA, obtained from: https://signalcaptchas.org/registration/generate.html")
    parser.add_argument("--verify", help="--verify NUMBER, number to verify")
    parser.add_argument("--code", help="--code CODE, 6 digit verification code.")
    parser.add_argument("--link", help="--link, Link an existing account.", action='store_true')
    parser.add_argument("--addContact", help="--addContct NUMBER add a contact.")
    parser.add_argument("--name", help="--name NAME, Contact name.")
    parser.add_argument("--account", help="--account ACCOUNTID, number of the account to use.")
    parser.add_argument("--doSend", help="--doSend NUMBER, send a test message to number.")
    parser.add_argument("--doSendGroup", help="--doSendGroup, Send a test message to c&c group", action='store_true')
    args = parser.parse_args()

    signal_config_path = '/home/streak/.local/share/signal-cli'
    # signal_config_path = "/home/streak/signal-cli"
    # signal_config_path = None
    log_file_path = '/home/streak/signal-cli/output.log'
    preview_url = 'https://thepostmillennial.com/balenciaga-tries-to-walk-back-ads-promoting-child-exploitation-by-suing-ad-creator'

    print("loading accounts")

    signal = SignalCli(signal_config_path)

    for account in signal.accounts:
        print(account.number)

    if args.register is not None:
        response = signal.register_account(args.register, args.captcha)
        if response[0]:
            print("Registration successful. Please verify.")
        else:
            print("Registration unsuccessful: %s" % response[1])
        exit(0)

    elif args.verify is not None:
        # Get unregistered accounts:
        account = signal.accounts.get_by_number(args.verify)
        if account is None:
            print("Unknown account: %s" % args.verify)
            exit(1)
        if account.registered:
            print("Account already registered.")
            exit(1)
        response = account.verify(args.code)
        print(response[0], response[1])
        exit(0)
    elif args.link:
        response = signal.start_link_account("SignalApi")
        print("LINK: ", response[0])
        print("QRCODE: \n", response[1])
        print("pngCode: ", response[2])

        response = signal.finsh_link()
        print(response)
        exit(0)
    elif args.addContact is not None:
        account = signal.accounts.get_by_number(args.account)
        print("Existing contacts:")
        for contact in account.contacts:
            print("name:", contact.name, "number:", contact.number, "uuid:", contact.uuid)
        (added, contact) = account.contacts.add("Peter N", args.addContact)
        print("Added:", added)
        print(contact)
        exit(0)

    account = signal.accounts.get_by_number(args.account)
    print("GROUPS:")
    for group in account.groups:
        print("Id: ", group.id, "Name: ", group.name)
    print("CONTACTS:")
    for contact in account.contacts:
        print(contact.get_display_name())

    if args.account == '+16134548055':
        print("Updating profile given name...")
        updated = account.profile.set_given_name("Peter's")
        print("Updated=", updated)
        print("Updating family name...")
        updated = account.profile.set_family_name("Bot")
        print("Updated=", updated)
        print("updating about...")
        updated = account.profile.set_about("Peter's bot account.")
        print("Updated=", updated)
        print("updateing about emoji to 🤖...")
        update = account.profile.set_emoji('🤖')
        print("Updated=", updated)

    signal.start_receive(account, all_msg_cb, received_msg_cb, receipt_msg_cb, sync_msg_cb, type_msg_cb, story_msg_cb, payment_msg_cb,
                         reaction_msg_cb)

    if args.doSend is not None:
        contact = account.contacts.get_by_id(args.doSend)
        preview = Preview(config_path=signal_config_path,
                          generate_preview=True,
                          url=preview_url)
        account.messages.send_message(
            recipients=contact,
            body="Test message.\n%s" % preview_url,
            preview=preview,
        )
        stickerPack = signal.sticker_packs.get_pack_by_name("Josh Saunders")
        sticker = stickerPack[0]
        account.messages.send_message(contact, sticker=sticker)

    # stickerPack = signal.stickers.get_by_name("Josh Saunders")
    # sticker = stickerPack[0]
    # account.messages.send_message(recipients=[recipient], sticker=sticker)
    if args.doSendGroup:
        marshJpg = '/home/streak/Pictures/marshmallow.jpg'
        groupId = "ECxpUY76Wwti8hxCfDmOgE9cZx2CCYHD1GxlWwwtFjs="
        group = account.groups.get_by_id(groupId)
        messageText = "This is a test.\n@<+16134548055>Please ignore.\n@<53bfafdc-9b22-4559-a7a6-1c8029f599d7>Also ignore."

        mentions = Mentions(contacts=account.contacts)
        mentions.create_from_body(messageText)

        results = account.messages.send_message(group, messageText, mentions=mentions, attachments=marshJpg)
        for result in results:
            print("Success:", result[0], "\tContact:", result[1].get_display_name(), "\tmessage:", result[2])

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nKeyboard Interrupt")
    signal.stopReceive(account)
    signal.stop_signal()
    exit(0)
