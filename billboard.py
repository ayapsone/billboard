# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.cloud import bigquery
from google.cloud import billing
from google.api_core.exceptions import BadRequest, AlreadyExists, NotFound
from google.cloud.exceptions import NotFound
import argparse, sys


bq_client = bigquery.Client()

report_base_url="https://datastudio.google.com/reporting/create?c.reportId=2e2ea000-8f68-40e2-8847-b80f05069b6e&r.reportName=MyBillboard"

standard_view_url="&ds.ds39.connector=bigQuery&ds.ds39.projectId={}&ds.ds39.type=TABLE&ds.ds39.datasetId={}&ds.ds39.tableId={}"
detailed_view_url="&ds.ds39.connector=bigQuery&ds.ds39.projectId={}&ds.ds39.type=TABLE&ds.ds39.datasetId={}&ds.ds39.tableId={}"
output_url=""

# This function checks if billboard dataset already exists or not
# so that we are not recreating it
def check_billboard_dataset_exists(dataset_id):

    try:
        bq_client.get_dataset(dataset_id)  # Make an API request.
        print("Dataset {} already exists so skipping creation.".format(dataset_id))
        return True
    except NotFound:
        print("Dataset {} is not found so creating it.".format(dataset_id))
        return False


# creates billboard dataset if does not exists on the location where billing is exported ( location )
# Location is taken from the billing export table provided by the user.
def create_dataset(args):

    #To be created dataset for billboard
    dataset_id = "{}.{}".format(args.project_id,args.bb_dataset_name)
    
    #Exported billing dataset
    source_id = "{}.{}.{}".format(args.project_id,args.dataset_name,args.standard_table)
   
    #check if billboard dataset exists
    if check_billboard_dataset_exists(dataset_id) == True:
        return

    # since we need to create, construct a full Dataset object to send to the API.
    dataset = bigquery.Dataset(dataset_id)

    #Need to create billboard dataset in the same location as exported dataset
    table_info = bq_client.get_table(source_id)
    dataset.location = table_info.location
    print("Exported BQ Table GEO Location={} so creating billboard dataset will be created in there as well.".format(table_info.location))
 
    
    # Send the dataset to the API for creation, with an explicit timeout.
    # Raises google.api_core.exceptions.Conflict if the Dataset already
    # exists within the project.
    dataset = bq_client.create_dataset(dataset, timeout=30)  # Make an API request.
    print("Created dataset {}".format(dataset_id))


# Creates the view for the Billboard
def create_billboard_view(args,isStandard):

    global output_url

    if isStandard == True:
        source_id="{}.{}.{}".format(args.project_id,args.dataset_name,args.standard_table)
        view_id="{}.{}.{}".format(args.project_id,args.bb_dataset_name,args.bb_standard)
    else:
        source_id="{}.{}.{}".format(args.project_id,args.detailed_dataset_name,args.detailed_table)
        view_id="{}.{}.{}".format(args.project_id,args.bb_dataset_name,args.bb_detailed)
  
    #Check resource detailed export is present
    try:      
        bq_client.get_table(source_id)
    except NotFound:
        if isStandard == True:
            print("Standard usage cost export not found="+source_id +" so skipping billboard view creation")
            sys.exit()
        else:
            print("Detailed usage cost export not found="+source_id +" so skipping billboard detailed view creation")
        return;

    sql = """
    CREATE VIEW if not exists `{}`
    AS select *, COALESCE((SELECT SUM(x.amount) FROM UNNEST(s.credits) x),0) AS credits_sum_amount, COALESCE((SELECT SUM(x.amount) FROM UNNEST(s.credits) x),0) + cost as net_cost, EXTRACT(DATE FROM _PARTITIONTIME) AS date from `{}` s WHERE _PARTITIONTIME >'2020-08-01'
    """.format(
        view_id,source_id
    )

    bq_view_client = bigquery.Client(project=args.project_id) #not sure why this need project_id

    job = bq_view_client.query(sql)  # API request.
    job.result()  # Waits for the query to finish.

    if isStandard == True:
        output_url=report_base_url+standard_view_url.format(args.project_id, args.bb_dataset_name,args.bb_standard)
    else:
        output_url=output_url+detailed_view_url.format(args.project_id, args.bb_dataset_name,args.bb_detailed)
 
    print(
        'Created view "{}.{}.{}".'.format(
            job.destination.project,
            job.destination.dataset_id,
            job.destination.table_id,
        )
    )

def generate_datastudio_url(args):

    print("\nUrls:")
    print("To view dataset, please click https://console.cloud.google.com/bigquery","\n")

    
    print("To launch datastudio report, please click ",output_url,"\n")

def remove_billboard_dataset(args):
    try:
        dataset_id = "{}.{}".format(args.project_id,args.bb_dataset_name)
        bq_client.delete_dataset(dataset_id,delete_contents=True, not_found_ok=True)
        print("Dataset {} deleted.".format(dataset_id))
        return True
    except NotFound:
        print("Dataset {} is not found.".format(dataset_id))
        return False    
    print("Cleaned")


def main(argv):

   parser = argparse.ArgumentParser(description='Billing Export information')
   parser.add_argument('-pr', dest='project_id', type=str, help='Project Id',required=True)
   parser.add_argument('-se', dest='dataset_name', type=str, help='Usage export dataset',required=True)
   parser.add_argument('-de', dest='detailed_dataset_name', type=str, help='Detailed Usage cost export dataset(if it\'s different than standard)')
   
   parser.add_argument('-bb', dest='bb_dataset_name', type=str, help='Billboard Dataset to be created',required=True)
   parser.add_argument('-bbs', dest='bb_standard', type=str, help='Billboard Standard View to be created',default="billboard")
   parser.add_argument('-bbd', dest='bb_detailed', type=str, help='Billboard Detailed View to be created',default="billboard_detail")

   parser.add_argument('-clean', dest='clean', type=str, help='To Remove Billboard Dataset, provide "yes"')
   

   args = parser.parse_args()
   if args.detailed_dataset_name == None:
       args.detailed_dataset_name = args.dataset_name

   project_billing_info =billing.CloudBillingClient().get_project_billing_info(name="projects/ayyappan-playground")
   billing_account_name= project_billing_info.billing_account_name.split("/")[1]
   print("Note: Script will use defaults if parameters are not passed for -bbs -bbd","\n")
   print("Project billing account="+billing_account_name,"\n")
   args.standard_table = "gcp_billing_export_v1_"+billing_account_name.replace('-','_')
   args.detailed_table = "gcp_billing_export_resource_v1_"+billing_account_name.replace('-','_')
   
   if args.clean == None:
       create_dataset(args)              #to create dataset
       create_billboard_view(args,True)  #to create standard view
       create_billboard_view(args,False) #to create detailed view
       generate_datastudio_url(args)     #to create urls
   else:
       remove_billboard_dataset(args)    #to cleanup

   
#main entry point
if __name__ == "__main__":
    main(sys.argv[1:])
