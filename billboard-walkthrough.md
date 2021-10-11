<h1>Overview</h1>
This code implements billboard dataset for standard and detailed billing



* **Environment set-up:**

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


<h1>Setup </h1>

* **Run locally:**
```
# help
python billboard.py -h


# Create billboard dataset where -se option is your standard billing export and -bb is billboard dataset to be created

python billboard.py -pr <your project id> -se <standard billing export dataset> -bb <billboard_dataset_name_to_be_created>

ex:
python billboard.py -pr <your project id> -se all_billing_data -bb billboard_ds

```

<h1> Clean up </h1>
#clean up
```
python billboard.py -pr <your project id> -se <standard billing export dataset> -bb <billboard_dataset_name_to_be_created> -clean yes

ex:
python billboard.py -pr <your project id> -se all_billing_data -bb billboard_ds -clean yes

```
