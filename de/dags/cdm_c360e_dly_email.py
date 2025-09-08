from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.email import send_email
from airflow.configuration import conf
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Configure logging
logger = logging.getLogger(__name__)

# Gmail configuration - Update these with your Gmail credentials
GMAIL_EMAIL = "nitt.kaditya@gmail.com"
GMAIL_APP_PASSWORD = ""  # Use App Password, not your regular Gmail password

# Or use environment variables (more secure):
# GMAIL_EMAIL = os.getenv('GMAIL_EMAIL', 'your-email@gmail.com')
# GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', 'your-app-password')

# Default arguments for the DAG
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,  # Disabled to prevent recursive errors
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
}

# Create the DAG
dag = DAG(
    'cdm_c360e_dly_email',
    default_args=default_args,
    description='Enhanced email DAG with Gmail SMTP fallback and error handling',
    schedule=None,
    catchup=False,
    tags=['notification', 'email', 'gmail', 'enhanced']
)

def send_email_with_gmail(to_emails, subject, html_content, from_email=None):
    """Send email using Gmail SMTP as fallback"""
    try:
        from_email = from_email or GMAIL_EMAIL
        
        # Ensure to_emails is a list
        if isinstance(to_emails, str):
            to_emails = ['data.akiran@gmail.com']
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        
        # Add HTML content
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Connect to Gmail SMTP
        logger.info("Connecting to Gmail SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable encryption
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(from_email, to_emails, text)
        server.quit()
        
        logger.info(f"Email sent successfully via Gmail to: {to_emails}")
        return True
        
    except Exception as e:
        logger.error(f"Gmail SMTP failed: {str(e)}")
        return False

def send_email_with_fallback(to_emails, subject, html_content):
    """Try Airflow's send_email first, then fallback to Gmail SMTP"""
    try:
        # First, try Airflow's built-in email function
        logger.info("Attempting to send email using Airflow's send_email...")
        send_email(
            to=to_emails,
            subject=subject,
            html_content=html_content
        )
        logger.info("Email sent successfully using Airflow's send_email")
        return True
        
    except Exception as e:
        logger.warning(f"Airflow send_email failed: {str(e)}")
        logger.info("Falling back to Gmail SMTP...")
        
        # Fallback to Gmail SMTP
        return send_email_with_gmail(to_emails, subject, html_content)

def send_custom_email(**context):
    """Send custom email with enhanced error handling"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Enhanced HTML content with better styling
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f5f5f5; 
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 0 auto; 
                    background-color: white; 
                    border-radius: 8px; 
                    overflow: hidden; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                }}
                .header {{ 
                    background: linear-gradient(135deg, #4285f4 0%, #34a853 100%); 
                    color: white; 
                    padding: 20px; 
                    text-align: center; 
                }}
                .content {{ 
                    padding: 20px; 
                }}
                .info-table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 15px 0; 
                }}
                .info-table td {{ 
                    padding: 8px 12px; 
                    border-bottom: 1px solid #eee; 
                }}
                .label {{ 
                    font-weight: bold; 
                    color: #333; 
                    width: 40%; 
                }}
                .status {{ 
                    background-color: #d4edda; 
                    color: #155724; 
                    padding: 10px; 
                    border-radius: 4px; 
                    text-align: center; 
                    margin: 15px 0; 
                }}
                .footer {{ 
                    background-color: #f8f9fa; 
                    padding: 15px 20px; 
                    text-align: center; 
                    color: #6c757d; 
                    font-size: 12px; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🚀 Airflow DAG Notification</h2>
                </div>
                
                <div class="content">
                    <p>This email was triggered from the Airflow DAG execution.</p>
                    
                    <table class="info-table">
                        <tr>
                            <td class="label">DAG ID:</td>
                            <td>{context['dag'].dag_id}</td>
                        </tr>
                        <tr>
                            <td class="label">Execution Date:</td>
                            <td>{context['ds']}</td>
                        </tr>
                        <tr>
                            <td class="label">Execution Time:</td>
                            <td>{current_time}</td>
                        </tr>
                        <tr>
                            <td class="label">DAG Run ID:</td>
                            <td>{context['dag_run'].run_id}</td>
                        </tr>
                        <tr>
                            <td class="label">Triggered at:</td>
                            <td>{context['ts']}</td>
                        </tr>
                    </table>
                    
                    <div class="status">
                        ✅ Task executed successfully
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated message from Apache Airflow.</p>
                    <p>Generated at {current_time}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email with fallback mechanism
        recipients = ['data.akiran@gmail.com']
        subject = f"Airflow DAG Triggered - {context['dag'].dag_id} - {context['ds']}"
        
        success = send_email_with_fallback(recipients, subject, html_content)
        
        if success:
            logger.info("✅ Custom email notification sent successfully")
            return "Email sent successfully"
        else:
            logger.error("❌ All email methods failed")
            return "Email sending failed - check configuration"
            
    except Exception as e:
        logger.error(f"Error in send_custom_email: {str(e)}")
        return f"Email task failed: {str(e)}"

def send_success_email(**context):
    """Send success confirmation email with DAG summary"""
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate some basic statistics
        total_tasks = len(context['dag'].task_dict)
        dag_tags = list(context['dag'].tags) if context['dag'].tags else []
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f5f5f5; 
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 0 auto; 
                    background-color: white; 
                    border-radius: 8px; 
                    overflow: hidden; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                }}
                .header {{ 
                    background: linear-gradient(135deg, #34a853 0%, #4285f4 100%); 
                    color: white; 
                    padding: 20px; 
                    text-align: center; 
                }}
                .content {{ 
                    padding: 20px; 
                }}
                .summary-box {{ 
                    background-color: #f8f9fa; 
                    border: 1px solid #dee2e6; 
                    border-radius: 6px; 
                    padding: 15px; 
                    margin: 15px 0; 
                }}
                .success-badge {{ 
                    background-color: #d1ecf1; 
                    color: #0c5460; 
                    padding: 10px; 
                    border-radius: 4px; 
                    text-align: center; 
                    margin: 15px 0; 
                    font-weight: bold; 
                }}
                .stats {{ 
                    display: flex; 
                    justify-content: space-around; 
                    margin: 20px 0; 
                }}
                .stat-item {{ 
                    text-align: center; 
                    flex: 1; 
                }}
                .stat-number {{ 
                    font-size: 24px; 
                    font-weight: bold; 
                    color: #34a853; 
                }}
                .stat-label {{ 
                    color: #6c757d; 
                    font-size: 12px; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📊 DAG Execution Summary</h2>
                </div>
                
                <div class="content">
                    <div class="success-badge">
                        🎉 DAG Execution Completed Successfully!
                    </div>
                    
                    <div class="summary-box">
                        <h3>Execution Details</h3>
                        <p><strong>DAG:</strong> {context['dag'].dag_id}</p>
                        <p><strong>Completion Time:</strong> {current_time}</p>
                        <p><strong>Execution Date:</strong> {context['ds']}</p>
                        <p><strong>Run ID:</strong> {context['dag_run'].run_id}</p>
                    </div>
                    
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-number">{total_tasks}</div>
                            <div class="stat-label">TOTAL TASKS</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">✓</div>
                            <div class="stat-label">STATUS</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{len(dag_tags)}</div>
                            <div class="stat-label">TAGS</div>
                        </div>
                    </div>
                    
                    <div class="summary-box">
                        <h4>What Happened:</h4>
                        <ul>
                            <li>All tasks in the DAG executed successfully</li>
                            <li>Email notifications were sent</li>
                            <li>Execution completed at {context['ts']}</li>
                        </ul>
                    </div>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 15px; text-align: center; color: #6c757d; font-size: 12px;">
                    <p>This summary was generated automatically by Apache Airflow.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        recipients = ['data.akiran@gmail.com']
        subject = f"✅ DAG Execution Complete - {context['dag'].dag_id}"
        
        success = send_email_with_fallback(recipients, subject, html_content)
        
        if success:
            logger.info("✅ Success summary email sent")
            return "Success email sent"
        else:
            logger.error("❌ Success email failed")
            return "Success email failed"
            
    except Exception as e:
        logger.error(f"Error in send_success_email: {str(e)}")
        return f"Success email task failed: {str(e)}"

# Task 1: Start task
start_task = EmptyOperator(
    task_id='start',
    dag=dag
)

# Task 2: Send main notification email
send_notification = PythonOperator(
    task_id='send_notification_email',
    python_callable=send_custom_email,
    dag=dag
)

# Task 3: Send success confirmation email
send_success = PythonOperator(
    task_id='send_success_notification',
    python_callable=send_success_email,
    dag=dag
)

# Task 4: End task
end_task = EmptyOperator(
    task_id='end',
    dag=dag
)

# Define task dependencies
start_task >> send_notification >> send_success >> end_task