import os
import smtplib
import socket
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

try:
    import socks
    HAS_SOCKS = True
except ImportError:
    HAS_SOCKS = False

if HAS_SOCKS:
    class SocksSMTP(smtplib.SMTP):
        def __init__(self, host='', port=0, local_hostname=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, proxy_type=None, proxy_addr=None, proxy_port=None):
            self.proxy_type = proxy_type
            self.proxy_addr = proxy_addr
            self.proxy_port = proxy_port
            super().__init__(host, port, local_hostname, timeout, source_address)

        def _get_socket(self, host, port, timeout):
            if self.proxy_type is not None and self.proxy_addr and self.proxy_port:
                s = socks.socksocket()
                s.set_proxy(self.proxy_type, self.proxy_addr, self.proxy_port)
                s.settimeout(timeout)
                s.connect((host, port))
                return s
            return super()._get_socket(host, port, timeout)

    class SocksSMTP_SSL(smtplib.SMTP_SSL):
        def __init__(self, host='', port=0, local_hostname=None, keyfile=None, certfile=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, context=None, proxy_type=None, proxy_addr=None, proxy_port=None):
            self.proxy_type = proxy_type
            self.proxy_addr = proxy_addr
            self.proxy_port = proxy_port
            super().__init__(host, port, local_hostname, keyfile, certfile, timeout, source_address, context)

        def _get_socket(self, host, port, timeout):
            if self.proxy_type is not None and self.proxy_addr and self.proxy_port:
                s = socks.socksocket()
                s.set_proxy(self.proxy_type, self.proxy_addr, self.proxy_port)
                s.settimeout(timeout)
                s.connect((host, port))
                # Wrap the socket with SSL
                import ssl
                if self.context is None:
                    self.context = ssl.create_default_context()
                return self.context.wrap_socket(s, server_hostname=host)
            return super()._get_socket(host, port, timeout)

class EmailSender:
    def __init__(self, smtp_server, smtp_port, sender_email, smtp_password, use_ssl=False,
                 proxy_enabled=False, proxy_type="SOCKS5", proxy_host="127.0.0.1", proxy_port=7890):
        self.smtp_server = smtp_server
        self.smtp_port = int(smtp_port)
        self.sender_email = sender_email
        self.smtp_password = smtp_password
        self.use_ssl = use_ssl
        self.proxy_enabled = proxy_enabled
        self.proxy_type = proxy_type
        self.proxy_host = proxy_host
        self.proxy_port = int(proxy_port) if proxy_port else 7890

    def _connect(self, timeout=120):
        """Helper to establish SMTP connection and authenticate."""
        if not self.smtp_server or not self.sender_email or not self.smtp_password:
            raise ValueError("发件配置不完整，请检查邮件SMTP设置！")

        proxy_t = None
        if self.proxy_enabled and HAS_SOCKS:
            proxy_t = socks.SOCKS5 if self.proxy_type == "SOCKS5" else socks.HTTP

        if self.use_ssl:
            if proxy_t:
                server = SocksSMTP_SSL(self.smtp_server, self.smtp_port, timeout=timeout,
                                       proxy_type=proxy_t, proxy_addr=self.proxy_host, proxy_port=self.proxy_port)
            else:
                # SSL Connection (typically port 465)
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=timeout)
        else:
            if proxy_t:
                server = SocksSMTP(self.smtp_server, self.smtp_port, timeout=timeout,
                                   proxy_type=proxy_t, proxy_addr=self.proxy_host, proxy_port=self.proxy_port)
            else:
                # TLS Connection (typically port 587)
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=timeout)
            
            server.ehlo()
            server.starttls()
            server.ehlo()
            
        server.login(self.sender_email, self.smtp_password)
        return server

    def test_connection(self):
        """Tests connection to the SMTP server. Returns (success, message)."""
        server = None
        try:
            server = self._connect(timeout=15)
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
            
            # Add header in RFC 2047 format to satisfy Amazon's strict, ancient parser
            from email.header import Header
            encoded_filename = Header(file_name, 'utf-8').encode()
            
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=encoded_filename
            )
            attachment.set_param('name', encoded_filename)
            msg.attach(attachment)

            # Connect and send (Using 180s timeout to allow large file transmission)
            server = self._connect(timeout=180)
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
