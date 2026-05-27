import os
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

class EmailSender:
    def __init__(self, smtp_server, smtp_port, sender_email, smtp_password, use_ssl=False):
        self.smtp_server = smtp_server
        self.smtp_port = int(smtp_port)
        self.sender_email = sender_email
        self.smtp_password = smtp_password
        self.use_ssl = use_ssl

    def _connect(self):
        """Helper to establish SMTP connection and authenticate."""
        if not self.smtp_server or not self.sender_email or not self.smtp_password:
            raise ValueError("发件配置不完整，请检查邮件SMTP设置！")

        if self.use_ssl:
            # SSL Connection (typically port 465)
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=15)
        else:
            # TLS Connection (typically port 587)
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            
        server.login(self.sender_email, self.smtp_password)
        return server

    def test_connection(self):
        """Tests connection to the SMTP server. Returns (success, message)."""
        server = None
        try:
            server = self._connect()
            return True, "连接并登录成功！您的SMTP邮箱设置是正确的。"
        except smtplib.SMTPAuthenticationError:
            return False, "登录失败！邮箱或密码/授权码(Auth Code)不正确。如果使用的是 Gmail 或 QQ 邮箱，必须使用专门生成的【应用专用密码/授权码】，而不是邮箱登录密码。"
        except smtplib.SMTPConnectError:
            return False, f"连接服务器失败！请检查 SMTP 服务器地址 ({self.smtp_server}) 或端口 ({self.smtp_port}) 是否正确，或者网络是否通畅。"
        except Exception as e:
            return False, f"测试失败，原因: {str(e)}"
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    def send_book(self, kindle_email, file_path, convert_pdf=True):
        """
        Sends an ebook to the Kindle email.
        If convert_pdf is True and the file is a PDF, sets the subject to 'Convert'
        to trigger Amazon's PDF conversion.
        Returns (success, message).
        """
        if not kindle_email:
            return False, "接收端 Kindle 邮箱未配置！"
        if not os.path.exists(file_path):
            return False, f"电子书文件不存在: {file_path}"

        server = None
        try:
            file_name = os.path.basename(file_path)
            
            # Create message container
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = kindle_email
            
            # If it's a PDF and convert is requested, Amazon recommends subject 'Convert'
            _, ext = os.path.splitext(file_name.lower())
            if ext == '.pdf' and convert_pdf:
                msg['Subject'] = 'Convert'
            else:
                msg['Subject'] = f'KindleFly Send: {file_name}'

            # Attach empty body (Kindle only cares about the attachment)
            msg.attach(MIMEText("", 'plain'))

            # Guess the MIME type or default to octet-stream
            ctype, encoding = mimetypes.guess_type(file_path)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)

            # Read file content and attach
            with open(file_path, 'rb') as fp:
                attachment = MIMEBase(maintype, subtype)
                attachment.set_payload(fp.read())
                
            # Encode in base64
            encoders.encode_base64(attachment)
            
            # Add header
            # To handle non-ASCII filenames in email headers correctly:
            # We encode the filename in UTF-8
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=('utf-8', '', file_name)
            )
            msg.attach(attachment)

            # Connect and send
            server = self._connect()
            server.sendmail(self.sender_email, [kindle_email], msg.as_string())
            
            return True, f"成功推送 '{file_name}' 至 Kindle!"
            
        except smtplib.SMTPAuthenticationError:
            return False, "发送失败：登录验证失败，请检查您的邮箱和密码/授权码。"
        except Exception as e:
            return False, f"发送失败，详细原因: {str(e)}"
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass
