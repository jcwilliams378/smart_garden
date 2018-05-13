# Import library and create instance of REST client.
from Adafruit_IO import Client
aio = Client('0e02f147a82e447a9efd431bdb757290')

# Send the value 100 to a feed called 'Foo'.
aio.send('foo', 100)

# Retrieve the most recent value from the feed 'Foo'.
# Access the value by reading the `value` property on the returned Data object.
# Note that all values retrieved from IO are strings so you might need to convert
# them to an int or numeric type if you expect a number.
data = aio.receive('foo')
print('Received value: {0}'.format(data.value))
