import re


def remove_emails_and_phone_numbers(text,
                                    email_placeholder='<email>',
                                    contact_num_placeholder='<contact_num>'):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\+?\d{1,3}?[-.\s]?\(?\d{1,4}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'

    text = re.sub(email_pattern, email_placeholder, text)  # mail
    text = re.sub(phone_pattern, contact_num_placeholder, text)  # phone
    text = re.sub(r'\s+', ' ', text).strip()

    return text
