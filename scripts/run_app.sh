# scripts/run_server.sh
#!/bin/bash
su -m app -c "python app.py"
# scripts/run_celery.sh
#!/bin/bash
su -m app -c "flask run" 
