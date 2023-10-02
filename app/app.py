from prometheus_client import start_http_server, Summary
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os
import json
import logging
import requests
import sys



logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def requests_with_error_handling(request_function,url,headers=None,params=None,data=None):
    logger.debug("Requesting URL:{}".format(url))
    try:
        response=request_function(url,headers=headers,params=params,data=data)
    except requests.exceptions.HTTPError as errh:
        logger.error("Http Error:{}".format(errh))
    except requests.exceptions.ConnectionError as errc:
        logger.error("Error Connecting:".format(errc))
    except requests.exceptions.Timeout as errt:
        logger.error("Timeout Error:".format(errt))
    except requests.exceptions.RequestException as errr:
        logger.error("OOps: Something Else".format(errr))
    except Exception as e:
        logger.error("Exception:{}".format(e))
    logger.debug("Returning Response")
    return(response)

if __name__ == '__main__':
    
    logger.info("Starting Cost Management Metrics Application")       
    # #https://access.redhat.com/articles/3626371#bgenerating-an-access-tokenb-4
    OFFLINE_TOKEN=os.environ.get('OFFLINE_TOKEN')
    DEFAULT_NAMESPACES=["hive","kube-","openshift-","open-cluster-management"]
    CLUSTER_NAME="rosa_4nbwt"
    KUBERNETES_SERVICE_HOST=os.environ.get('KUBERNETES_SERVICE_HOST')
    KUBERNETES_SERVICE_PORT=os.environ.get('KUBERNETES_SERVICE_PORT')
    TOKEN_REQUEST_URL="https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token"
    TOKEN_REQUEST_DATA={'grant_type':'refresh_token',
                   'client_id':'rhsm-api',
                   'refresh_token':"{}".format(OFFLINE_TOKEN)}

                  

    token_response=requests_with_error_handling(requests.post,TOKEN_REQUEST_URL,data=TOKEN_REQUEST_DATA)
    token_temp=token_response.json()

    if "error" in token_temp:        
        logger.error("Error: {}".format(token_temp['error']))
        if "error_description" in token_temp:
            logger.error("Error Description: {}".format(token_temp['error_description']))
        sys.exit(1)
    else:
        if "access_token" in token_temp:
            logger.info("Token Retrieved")
            TOKEN=token_temp['access_token']
        else:
            logger.error("Error: Could not retrieve token")
            sys.exit(1)
        
    
    COST_REQUEST_URL="https://console.redhat.com/api/cost-management/v1/reports/openshift/costs/"
    COST_REQUEST_HEADER= {
        'Authorization': f"Bearer {TOKEN}",
        'Accept': 'application/json',
    }

    COST_REQUEST_PARAMS = (
        ('filter[time_scope_units]', 'month'),
        ('filter[time_scope_value]', '-1'),
        ('filter[resolution]', 'monthly'),
        # ('filter[cluster]', CLUSTER_NAME),
        ('group_by[project]', '*'),
    )

    cost_response = requests_with_error_handling(requests.get,COST_REQUEST_URL, headers=COST_REQUEST_HEADER, params=COST_REQUEST_PARAMS)
    # with open('cost_response_project.json', 'w') as outfile:
    #     outfile.write(cost_response.text)
    cost_response_project = cost_response.json()
    
    # with open('cost_response_project.json') as json_file:
    #     cost_response_project = json.load(json_file)
 
    # with open('cost2_response_project.json','w') as outfile:
    #     outfile.write(json.dumps(cost_response_project["data"][0]["projects"]))    
    
    try:
        config.load_kube_config()  
    except Exception as e:
        logger.error("Exception Loading Kubeconfig:{}".format(e))
        sys.exit(1)
    
    api_instance = client.CoreV1Api()
    try:
        cluster_namespaces = api_instance.list_namespace()
    except ApiException as e:
        logger.error("Exception when calling CoreV1Api: {}".format(e))
        sys.exit(1)
    except Exception as e:
        logger.error("Exception when calling CoreV1Api: {}".format(e))
        sys.exit(1)
        
    for namespace in cluster_namespaces.items:
        is_default_namespace = False
        for default_namespace in DEFAULT_NAMESPACES:
            if default_namespace in namespace.metadata.name:
                is_default_namespace = True

        if not is_default_namespace:
            print(namespace.metadata.name)
            
            testfilter=list(filter(lambda project: project['project'] == namespace.metadata.name, cost_response_project["data"][0]["projects"]))
            if len(testfilter) > 0:
                
                print(testfilter[0]['values'][0]['cost']['distributed']['value'])
                print(namespace.metadata.name)
                #body='{{"metadata":{{"labels":{{"cost":"{}"}} }} }}'.format(testfilter[0]['values'][0]['cost']['total']['value'])
                body = [{"op": "replace", "path": "/metadata/labels/monthly_cost_example", "value": "{}".format(testfilter[0]['values'][0]['cost']['distributed']['value'])}]
                api_instance.patch_namespace(namespace.metadata.name, body)
                
