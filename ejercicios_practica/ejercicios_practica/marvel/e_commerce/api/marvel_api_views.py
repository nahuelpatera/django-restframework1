# Import models:
from e_commerce.models import *

from marvel.settings import VERDE, CIAN, AMARILLO
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import hashlib

# NOTE: Declaramos las variables que tienen que ver con la API KEY de Marvel:

PUBLIC_KEY = '65933cf1b1cd88a31b3c0ad4961c8e6f'
PRIVATE_KEY = 'a22ca6d0e9f8a74a509759aef7f25642a3735d7d'
TS = 1
TO_HASH = str(TS)+PRIVATE_KEY+PUBLIC_KEY
HASHED = hashlib.md5(TO_HASH.encode())
URL_BASE = 'http://gateway.marvel.com/v1/public/'
ENDPOINT = 'comics'
PARAMS = dict(ts=TS, apikey=PUBLIC_KEY, hash=HASHED.hexdigest())


@csrf_exempt
def get_comics(request):
    '''
    Vista personalizada de API para comprar comics, 
    primero consultamos los comics disponibles en la página de Marvel, 
    luego generamos una lista de los que tienen precio y descripción, 
    porque varios vienen `null`.
    '''
    # Declaramos nuestras variables:
    id = []
    title = []
    description = []
    prices = []
    thumbnail = []
    limit = 0
    offset = 0
    # NOTE: Para obtener los valores de request, dependemos del tipo de petición, así:
    # GET METHOD: request.GET['algo']   O también: request.GET.get('algo')
    # POST METHOD: request.POST['algo'] O también: request.POST.get('algo')
    # POST METHOD: request.data['algo'] O también: request.data.get('algo')
    # Como son similares a los diccionarios se puede hacer de las dos maneras.

    # Traemos los datos del request, asegurandonos que son numeros, sino, les asignamos
    # un valor por defecto:
    if request.GET.get('offset') == None or request.GET['offset'].isdigit() == False:
        offset = 0
    else:
        offset = request.GET.get('offset')
    if request.GET.get('limit') == None or request.GET['limit'].isdigit() == False:
    #  if not request.GET.get('limit') or not request.GET['limit'].isdigit():
        limit = 15
    else:
        limit = request.GET.get('limit')

    offset = int(offset)
    limit = int(limit)

    # Realizamos el request:
    aditional_params = {'limit': limit, 'offset': offset}
    params = PARAMS
    params.update(aditional_params)
    # NOTE: A los parametros de hash, api key y demás, sumamos limit y offset para paginación.
    res = requests.get(URL_BASE+ENDPOINT, params=params)
    comics = json.loads(res.text)

    # Obtenemos la lista de comics del json:
    comics_list = comics.get('data').get('results')

    # Filtramos la lista de comics y nos quedamos con lo que nos interesa:
    for comic in comics_list:
        id.append(comic.get('id'))
        description.append(comic.get('description'))
        title.append(comic.get('title'))
        prices.append(comic.get('prices')[0].get('price'))
        thumbnail.append(
            f"{comic.get('thumbnail').get('path')}/standard_xlarge.jpg")

    # NOTE: Construimos la tabla, concatenando en un string el código HTML:

    template = '''<div>
    <div style="height:90%; width:90%; overflow:auto;background:gray;">
        <table>'''

    for i in range(len(id)):
        if description[i] == None:
            desc = "<h3>Description Not Available<h3>"
        else:
            desc = description[i]

        if prices[i] == 0.00:
            # Con este condicional inhabilitamos la compra de los comics sin precio.
            price = "<h3>N/A<h3>"
            visibility = "hidden"
        else:
            price = prices[i]
            visibility = "visible"

        template += f'''
        <tr>
        <td>
            <img src="{thumbnail[i]}">
        </td>
        <td>    
            <h2>{title[i]}</h2><br><br>
            {desc}
        </td>
        <td><h2>U$S{price}</h2></td>
        <td>
            <form action="/e-commerce/purchased-item/" method="post" , style ="visibility: {visibility};">
                <label for="qty"><h3>Enter Quantity:</h3></label>
                <input type="number" id="qty" name="qty" min="0" max="15">
                <input type="submit" value="Buy" >
                <input type="text" name="id" value="{id[i]}" style="visibility: hidden">
                <input type="text" name="title" value="{title[i]}" style="visibility: hidden">
                <input type="text" name="thumbnail" value="{thumbnail[i]}" style="visibility: hidden">
                <input type="text" name="description" value="{description[i]}" style="visibility: hidden">
                <input type="text" name="prices" value="{prices[i]}" style="visibility: hidden">
            </form>
        </td>
        </tr>
        
        '''
    template += f'</table></div></div>'
    # Imprimimos por consola el HTML construido (se puede probar en https://codepen.io/):
    print(template)
    # O lo podemos guardar en un HTML, como el nombre no cambia, el archivo se pisa en cada petición:
    f = open('get_comics.html','w')
    f.write(template)
    f.close
    return HttpResponse(template)

@csrf_exempt
def purchased_item(request):
    '''Incluye la lógica de guardar lo pedido en la base de datos 
    y devuelve el detalle de lo adquirido '''

    # Obtenemos los datos del request:
    title = request.POST.get('title')
    thumbnail = request.POST.get('thumbnail')
    description = request.POST.get('description')
    price = request.POST.get('prices')
    qty = request.POST.get('qty')
    id = request.POST.get('id')

    # Verificamos si el comic no se encuentra en nuestro stock.
    # Para eso hacemos uso del método ".get_or_create()".
    # En caso de existir, actualizamos su cantidad.
    _comic, _created = Comic.objects.get_or_create(
        marvel_id=id,
        defaults={
            'title': title,
            'description': description,
            'price': price,
            'stock_qty': qty,
            'picture': thumbnail,
            'marvel_id': id
        }
    )
    if not _created:
        _comic.stock_qty += int(qty)
        _comic.save()

    # NOTE: Construimos la respuesta
    # Calculamos el precio total:
    try:
        total = float(price) * int(qty)
    except:
        total = ". . ."
    # Creamos en una tabla la respuesta del comic comprado,
    # con precio unitario y precio total:
    template = f'''
    <h1>
    Your purchased product:
    </h1>
    <table>
    <tr>
        <td>
        <img src="{thumbnail}">
        </td>
        <td>
            <ul>
                <li><h2>{title}</h2></li>
                <li>ID: {id}</li>
                <li>Description: {description}</li>
                <li>Price (each): U$S{price}</li>
                <li>Qty.: {qty}</li>
                <li><h3>Total: U$S {total:.2f}</h3></li>
            </ul>
        </td>
    <tr>
    </table>
    '''
    # Imprimimos por consola el HTML construido (se puede probar en https://codepen.io/):
    print(VERDE+template)
    return HttpResponse(template)
