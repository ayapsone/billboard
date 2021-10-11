# Overview
This code implements billboard dataset for standard and detailed billing



##Environment set-up

You can set-up the right python environment as follows:

```
pip install virtualenv
virtualenv bill-env
source bill-env/bin/activate
pip install -r requirements.txt

```

This step includes the following:
- Install Python local env
- Launch local env
- Install dependencies

To get command options
```
python billboard.py -h
```

 To create billboard dataset
```
python billboard.py -pr <project id> -se <standard billing ds> -bb <billboard_ds>
```

To clean up
```
python billboard.py -pr <project id> -se <standard billing ds> -bb <billboard_ds> -clean yes

```
