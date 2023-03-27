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

def allMsgCb(account: Account, message:ReceivedMessage|Receipt|TypingMessage|SyncMessage):
    # print("ALL")
    # print(message)
    return

def receivedMsgCb(account:Account, message:ReceivedMessage):
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
    if (message.quote != None):
        if (message.quote.attachments != None):
            for attachment in message.quote.attachments:
                displayName = "<UNKNOWN-ATTACHMENT>"
                if (attachment.file_name != None and attachment.file_name != ''):
                    displayName = attachment.file_name
                elif (attachment.local_path != None and attachment.exists == True):
                    displayName = attachment.local_path
                elif (attachment.thumbnail != None and attachment.thumbnail.exists == True):
                    displayName = "Thumbnail: %s" % attachment.thumbnail.localPath
                print("Trying to display attachment: %s...\n    Success=" % displayName, end='', flush=True)
                # returnValue = attachment.display()
                # print(returnValue)

        quotedMessage = account.messages.get_quoted(message.quote)
        if (quotedMessage == None):
            print("Quoting a message not found in history.")
        else:
            if (isinstance(quotedMessage, ReceivedMessage) == True):
                print("Quoting received message FROM:%s AT: %s" % (quotedMessage.sender.get_display_name(),
                                                                    quotedMessage.timestamp.get_display_time()))
                if (quotedMessage.recipient_type == 'group'):
                    print("in GROUP: %s" % quotedMessage.recipient.get_display_name())
            elif (isinstance(quotedMessage, SentMessage) == True):
                print("Quoting message sent AT: %s" % quotedMessage.timestamp.get_display_time())
                if (quotedMessage.recipient_type == 'group'):
                    print("In GROUP: %s" % quotedMessage.recipient.get_display_name())
        quotedText = message.quote.parse_mentions()
        print("Quoted TEXT: %s" % quotedText)

    print("--------Begin Message--------")
    displayText = message.parse_mentions()
    print(displayText)
    print("---------End Message---------")


    if (message.attachments != None):
        for attachment in message.attachments:
            displayName = "<UNKNOWN-ATTACHMENT>"
            if (attachment.file_name != None and attachment.file_name != ''):
                displayName = attachment.file_name
            elif (attachment.local_path != None and attachment.exists == True):
                displayName = attachment.local_path
            elif (attachment.thumbnail != None and attachment.thumbnail.exists == True):
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

def receiptMsgCb(account, message: Receipt):
    print("RECEIPT")
    print(message.body)
    return

def syncMsgCb(account, message):
    print("SYNC")
    print(message)
    return

def typeMsgCb(account, message: TypingMessage):
    print("TYPING")
    print(message.body)
    return

def storyMsgCb(account, message):
    print("STORY")
    print(message)
    return

def paymentMsgCb(account, message):
    print("PAYMENT")
    print(message)
    return

def reactionMsgCb(account, message:Reaction):
    print("REACTION")
    print(message.body)
    return

def callMsgCb(account, message):
    print("CALL")
    print(message)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Signal test code.")
    parser.add_argument("--register", help="--register NUMBER, number to register.")
    parser.add_argument("--captcha", help="--captcha CAPTCHA, obtained from: https://signalcaptchas.org/registration/generate.html")
    parser.add_argument("--verify", help="--verify NUMBER, number to verify")
    parser.add_argument("--code", help="--code CODE, 6 digit verification code.")
    parser.add_argument("--link", help="--link, Link an existing account.", action='store_true')
    parser.add_argument("--addContact", help="--addContct NUMBER add a contact.")
    parser.add_argument("--name", help="--name NAME, Contact name.")
    parser.add_argument("--account", help="--account ACCOUNTID, number of the account to use.")
    parser.add_argument("--doSend", help="--doSend NUMBER, send a test message to number.")
    parser.add_argument("--doSendGroup", help="--doSendGroup, Send a test message to c&c group", action='store_true')
    args = parser.parse_args()

    signalConfigPath = '/home/streak/.local/share/signal-cli'
    # signal_config_path = "/home/streak/signal-cli"
    # signal_config_path = None
    logFilePath = '/home/streak/signal-cli/output.log'
    previewUrl = 'https://thepostmillennial.com/balenciaga-tries-to-walk-back-ads-promoting-child-exploitation-by-suing-ad-creator'

    print("loading accounts")

    signal = SignalCli(signalConfigPath)

    for account in signal.accounts:
        print (account.number)

    if (args.register != None):
        response = signal.register_account(args.register, args.captcha)
        if (response[0] == True):
            print ("Registration successful. Please verify.")
        else:
            print("Registration unsuccessful: %s" % response[1])
        exit(0)

    elif (args.verify != None):
    # Get unregistered accounts:
        account = signal.accounts.get_by_number(args.verify)
        if (account == None):
            print("Unknown account: %s" % args.verify)
            exit(1)
        if (account.registered == True):
            print("Account already registered.")
            exit(1)
        response = account.verify(args.code)
        print(response[0], response[1])
        exit(0)
    elif( args.link == True):
        response = signal.start_link_account("SignalApi")
        print("LINK: ", response[0])
        print("QRCODE: \n", response[1])
        print("pngCode: ", response[2])

        response = signal.finsh_link()
        print (response)
        exit(0)
    elif (args.addContact != None):
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
        print ("Id: ", group.id, "Name: ", group.name)
    print("CONTACTS:")
    for contact in account.contacts:
        print(contact.get_display_name())

    if (args.account == '+16134548055'):
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

    signal.start_receive(account, allMsgCb, receivedMsgCb, receiptMsgCb, syncMsgCb, typeMsgCb, storyMsgCb, paymentMsgCb,
                         reactionMsgCb)

    

    if (args.doSend != None):
        contact = account.contacts.get_by_id(args.doSend)
        preview = Preview(config_path=signalConfigPath,
                          generate_preview=True,
                          url=previewUrl)
        account.messages.send_message(
                recipients=contact,
                body="Test message.\n%s" % previewUrl,
                preview=preview,
            )
        stickerPack = signal.sticker_packs.get_pack_by_name("Josh Saunders")
        sticker = stickerPack[0]
        account.messages.send_message(contact, sticker=sticker)
    

    # stickerPack = signal.stickers.get_by_name("Josh Saunders")
    # sticker = stickerPack[0]
    # account.messages.send_message(recipients=[recipient], sticker=sticker)
    if (args.doSendGroup == True):
        marshJpg = '/home/streak/Pictures/marshmallow.jpg'
        groupId = "ECxpUY76Wwti8hxCfDmOgE9cZx2CCYHD1GxlWwwtFjs="
        group = account.groups.get_by_id(groupId)
        messageText = "This is a test.\n@<+16134548055>Please ignore.\n@<53bfafdc-9b22-4559-a7a6-1c8029f599d7>Also ignore."

        mentions = Mentions(contacts=account.contacts)
        mentions.create_from_body(messageText)

        results = account.messages.send_message(group, messageText, mentions=mentions, attachments=marshJpg)
        for result in results:
            print ("Success:", result[0], "\tContact:", result[1].get_display_name(), "\tmessage:", result[2])

    try:
        while (True):
            pass
    except KeyboardInterrupt:
        print("\nKeyboard Interrupt")
    signal.stopReceive(account)
    signal.stop_signal()
    exit(0)