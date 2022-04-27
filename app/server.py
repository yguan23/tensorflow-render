import aiohttp
import asyncio
import uvicorn
from fastai import *
from fastai.vision import *
import tensorflow as tf
from PIL import Image
from tensorflow import keras
from tensorflow.keras.applications.densenet import DenseNet121, preprocess_input
import numpy as np
#from tensorflow.keras.utils.data_utils import get_file
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles


#set url
# export_file_url = 'https://drive.google.com/uc?export=download&id=1ZZ_2JRe39KcgqGu75watpeLOtQGfeDPA'
model_config_name = 'app/models/model.config'
model_file_name = 'app/models/best_model.h5'

classes = ['0', '1', '2', '3', '4']
# classes = ['檸檬', '柑', '葡萄柚', '柳丁', '金桔']
path = Path(__file__).parent
# data_list["label"] = classes["label_name"].map(class_map)
img_size = 224
app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    # await download_file(export_file_url, path / export_file_name)
    try:
        #learn = load_learner(path, export_file_name)        
        #learn = keras.models.load_model("app/"+export_file_name)
        with open(model_config_name, "r") as text_file:
            json_string = text_file.read()
        learn = keras.models.model_from_json(json_string)
        learn.load_weights(model_file_name)
        #learn = keras.models.load_model(model_path)
        
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
#     img = open_image(BytesIO(img_bytes))   
#     prediction = learn.predict(img)[0]
#     image = tf.keras.preprocessing.image.load_img( path, target_size=(img_size, img_size))
#     input_arr = keras.preprocessing.image.img_to_array(image)
#     input_arr = np.array([input_arr])  # Convert single image to a batch.
#     predictions = learn.predict(input_arr) 

    img = Image.open(BytesIO(img_bytes))
    img = img.convert('RGB')
    img = img.resize((img_size, img_size), Image.NEAREST)
    img = np.array(img)
#     np.array(img) = ['檸檬', '柑', '葡萄柚', '柳丁', '金桔']
    img = preprocess_input( np.array([img]) )
    predictions = learn.predict(img)  
    prediction = predictions.argmax()
    
#     data_list = pd.DataFrame({"img_path":img_list, "label_name":data_label, "types":data_types})
#     img['label_list'] = ['檸檬', '柑', '葡萄柚', '柳丁', '金桔']
#     img['label_list'] = str(prediction).map(img)
#     return JSONResponse({'result': img['label_list']})

    if str(prediction) == 0:
        str result = '檸檬'
    elif str(prediction) == 1:
        str result = '柑'
    elif str(prediction) == 2:
        str result= '葡萄柚'
    elif str(prediction) == 3:
        str result = '柳丁'
    else:
        str result = '金桔'
        
    return JSONResponse({'result': str(prediction), ' ': result})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5001, log_level="info")
