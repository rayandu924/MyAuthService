next upgrade will be one time code connexion

# Development

## Setup

### Install Python

```bash
sudo apt-get install python3
```

### Install Pip

```bash
sudo apt-get install python3-pip
```

### Install Virtualenv

```bash
sudo pip3 install virtualenv
```

### Create Virtual Environment

```bash
virtualenv venv
```

### Activate Virtual Environment

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Set Dependencies

```bash
pip freeze > requirements.txt
```

### Run Application From Root Directory

```bash
python -m app.server
```
