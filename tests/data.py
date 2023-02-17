
# number, description
# taken from the August 2020, UPS Tracking Tracking Web Service Developer Guide, pg. 13
UPS_TEST_NUMBERS = {
    '1Z12345E0205271688': '(Signature Availability), 2nd Day Air, Delivered',
    '1Z12345E6605272234': 'World Wide Express, Delivered',
    '1Z12345E0305271640': '(Second Package: 1Z12345E0393657226), Ground, Delivered',
    '1Z12345E1305277940': 'Next Day Air Saver, ORIGIN SCAN',
    '1Z12345E6205277936': 'Next Day Air Saver, 2nd Delivery attempt',
    '1Z648616E192760718': 'UPS Worldwide Express Freight, Order Process by UPS',
    '1ZWX0692YP40636269': 'UPS SUREPOST, Response for UPS SUREPOST',
}
UPS_FAIL_NUMBER = '1Z12345E1505270452'  # No Tracking Information Available
UPS_BOGUS_NUMBER = '1Z12345E020527079'


FEDEX_TEST_NUMBERS = {
    '122816215025810': 'Delivered',
    '449044304137821': 'Shipment information sent to FedEx',
    '149331877648230': 'Tendered',
    '020207021381215': 'Picked Up',
    '403934084723025': 'Arrived at FedEx location',
    '920241085725456': 'At local FedEx facility',
    '568838414941':     'At destination sort facility',
    '039813852990618': 'Departed FedEx location',
    '231300687629630': 'On FedEx vehicle for delivery',
    '797806677146':     'International shipment release',
    '377101283611590': 'Customer not available or business closed',
    '852426136339213': 'Local Delivery Restriction',
    '797615467620':     'Incorrect Address',
    '957794015041323': 'Unable to Deliver',
    '076288115212522': 'Returned to Sender/Shipper',
    '581190049992':     'International Clearance delay',
    '843119172384577': 'Hold at Location',
    '070358180009382': 'Shipment Canceled',
}

DHL_TEST_NUMBERS = {
    '7777777770': 'transit',
}
DHL_TEST_FORMATS = [
    '0004567890',           # DHL Express
    'JJD0123456',           # DHL Express
    'JJD0012345',           # DHL Express
    'JVGL123456',           # DHL Express
    '3S12345678',           # DHL Parcel
    'JJD1234567',           # DHL Parcel
    'GM00000000',           # DHL eCommerce
    'LX0000000000000',      # DHL eCommerce
    'RX00000000000000000',  # DHL eCommerce
]
# I made this one up
DHL_FAIL_NUMBER = '7777777771'


USPS_TEST_NUMBERS = {
    '9400100000000000000000':   'USPS Tracking',
    '9205500000000000000000':   'Priority Mail',
    '82 000 000 00':            'Global Express Guaranteed',
    'EC 000 000 000 US':        'Priority Mail International',
}
USPS_BOGUS_NUM = '9405503699300451134169'
USPS_REAL_PACKAGES = [
    'LM181476342CA',
]
