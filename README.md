# Hephaestus-Chatbot



API IMDb (notes de films / séries) :

```py
import http.client

conn = http.client.HTTPSConnection("imdb236.p.rapidapi.com")

headers = { 'x-rapidapi-host': "imdb236.p.rapidapi.com" }

conn.request("GET", "/api/imdb/cast/nm0000190/titles", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
```


API Streaming availability (où regarder le film) : 

```py
import http.client

conn = http.client.HTTPSConnection("streaming-availability.p.rapidapi.com")

headers = { 'x-rapidapi-host': "streaming-availability.p.rapidapi.com" }

conn.request("GET", "/shows/%7Btype%7D/%7Bid%7D", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
```

