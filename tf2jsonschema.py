import click
import glob
import hcl2
import re
import yaml


@click.command()
@click.argument('tfdir')
def generate_schema(tfdir):
    """
    Read terraform files in `tfdir` and generate schema from variables
    """
    resource_name = 'test-resource'
    resource_title = 'test resource'
    content = concat_tf(tfdir)
    # print('Read {}'.format(content))
    tf = hcl2.loads(content)
    jsonschema = {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        'title': 'Generic title',
        'description': 'Generic description',
    }
    for variableitem in tf['variable']:
        parse_variables(jsonschema, variableitem)
     
    openapi = {
        'openapi': '3.1.0',
        'info': {
            'title': resource_title,
        },
        'paths': {
            '/{}'.format(resource_name): {
                'post': {
                    'requestBody': {
                        'content': {
                            'application/json': {
                                'schema': jsonschema
                            }
                        }
                    }
                    
                }
            }
        }
    }
    
    print(yaml.dump(openapi))

def parse_variables(dict, variables):
    for name, variable in variables.items():
        prop = {}
        if 'description' in variable:
            prop['description'] = variable['description']
        if 'type' in variable:
            parse_object_type(prop, name, variable)
        if 'default' in variable:
            prop['default'] = variable['default']


        if 'properties' not in dict:
            dict['properties'] = {}
        dict['properties'][name] = prop

def parse_object_type(dict, name, variable):
    dict['type'] = tojsonschematype(variable['type'])

    # maptype = re.search(r"(map|object)\((.*)\)", variable['type'])
    # if maptype is not None:
    #     inner_type = maptype.group(2)
    #     print("inner: {}".format(inner_type))
    #     prop = {}

    #     type_def = re.search(r"{.*}", inner_type)
        
    # # '(.*)': '(.*)'
    #     dict['properties'][name] = prop


def tojsonschematype(tftype):
    """
    Convert a terraform type into a jsonschema type
    Terraform types taken from https://developer.hashicorp.com/terraform/language/expressions/types
    Jsonschema types from https://json-schema.org/understanding-json-schema/reference/
    """
    maptype = re.search(r"(map|object)\((.*)\)", tftype)
    arraytype = re.search(r"(list|tuple)\((.*)\)", tftype)
    if tftype == '${string}':
        return 'string'
    elif tftype == '${bool}':
        return 'boolean'
    elif tftype == '${number}':
        return 'number'
    elif maptype != None:
        return 'object'
    elif arraytype != None:
        return 'array'
    return tftype


def concat_tf(tfdir):
    """
    Concatenate all the .tf files in `tfdir`
    """
    content = ""
    for filename in glob.glob("{}/*.tf".format(tfdir)):
      with open(filename, 'r') as file:
          content = content + file.read() + '\n'

    return content


if __name__ == "__main__":
    generate_schema()
