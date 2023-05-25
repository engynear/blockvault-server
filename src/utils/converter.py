import json
import base64
from PIL import Image

def bbmodel_to_json(input_file, output_dir, output_file):
    with open(input_file, 'r') as f:
        bbmodel = json.load(f)

    format = bbmodel['meta']['model_format']

    if format == 'java_block':
        bbmodel_java_to_json(bbmodel, output_dir, output_file)
    elif format == 'bedrock':
        bbmodel_bedrock_to_json(bbmodel, output_dir, output_file)
    elif format == 'free':
        bbmodel_free_to_json(bbmodel, output_dir, output_file)
    else:
        raise Exception('Unknown format: {}'.format(format))

def bbmodel_java_to_json(bbmodel, output_dir, output_file):
    textures = {}
    for texture in bbmodel['textures']:
        if texture['id'] == '0' or texture['particle']:
            image_data = base64.b64decode(texture['source'].split(',')[1])
            image_path = '{}/{}.png'.format(output_dir, texture['uuid'])
            with open(image_path, 'wb') as img_file:
                img_file.write(image_data)
            textures[texture['id']] = image_path

    elements = []
    for element in bbmodel['elements']:
        faces = {}
        for face, data in element['faces'].items():
            uv = data['uv']
            texture = '#' + str(data['texture'])
            faces[face] = {'uv': uv, 'texture': texture}
        new_element = {
            'from': element['from'],
            'to': element['to'],
            'rotation': element.get('rotation', {}),
            'rescale': element.get('rescale', False),
            'mirror_uv': element.get('box_uv', False),
            'shade': element.get('shade', True),
            'faces': faces
        }
        elements.append(new_element)
        
    result = {
        'credit': 'Made with Blockbench',
        'texture_size': [bbmodel['resolution']['width'], bbmodel['resolution']['height']],
        'textures': textures,
        'elements': elements
    }

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)


bbmodel_to_json("test1.bbmodel", ".", "test.json")

