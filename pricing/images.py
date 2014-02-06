def get_airline_info(name):

  #code = code.upper

  airlines = {
    'EIN' : {'name': 'Aer Lingus', 'short_name':'Aer Lingus', 'image': 'aer-lingus.gif'},
    'AFL' : {'name': 'Aeroflot Russian Airlines', 'short_name':'Aeroflot', 'image': 'aeroflot.gif'},
    'ARG' : {'name': 'Aerolineas Argentinas', 'short_name':'Aerolineas', 'image': 'aerolineas-argentinas.png'},
    'AMX' : {'name': 'Aeromexico', 'short_name':'Aeromexico', 'image': 'aeromexico.jpg'},
    'ABY' : {'name': 'Air Arabia', 'short_name':'Air Arabia', 'image': 'air-arabia.jpg'},
    'AXM' : {'name': 'AirAsia', 'short_name':'AirAsia', 'image': 'air-asia.png'},
    'BER' : {'name': 'Air Berlin', 'short_name':'Air Berlin', 'image': 'air-berlin.gif'},
    'ACA' : {'name': 'Air Canada', 'short_name':'Air Canada', 'image': 'air-canada.jpg'},
    'CCA' : {'name': 'Air China', 'short_name':'Air China', 'image': 'air-china.jpg'},
    'AFR' : {'name': 'Air France', 'short_name':'Air France', 'image': 'air-france.jpg'},
    'AIC' : {'name': 'Air India Limited', 'short_name':'Air India', 'image': 'air-india.jpg'},
    'MDG' : {'name': 'Air Madagascar', 'short_name':'Air Madagascar', 'image': 'air-madagascar.gif'},
    'MAU' : {'name': 'Air Mauritius', 'short_name':'Air Mauritius', 'image': 'air-mauritius.jpg'},
    'ANZ' : {'name': 'Air New Zealand', 'short_name':'Air New Zealand', 'image': 'air-new-zealand.jpg'},
    'ANE' : {'name': 'Air Nostrum', 'short_name':'Air Nostrum', 'image': 'air-nostrum.jpg'},
    'GAP' : {'name': 'Air Philippines', 'short_name':'Air Philippines', 'image': 'air-philippines.gif'},
    'SEY' : {'name': 'Air Seychelles', 'short_name':'Air Seychelles', 'image': 'air-seychelles.png'},
    'TSC' : {'name': 'Air Transat', 'short_name':'Air Transat', 'image': 'air-transat.jpg'},
    'TRS' : {'name': 'AirTran Airways', 'short_name':'AirTran', 'image': 'airtran.jpg'},
    'PAK' : {'name': 'Alaska Airlines', 'short_name':'Alaska', 'image': 'alaska-airlines.gif'},
    'AZA' : {'name': 'Alitalia', 'short_name':'Alitalia', 'image': 'alitalia.gif'},
    'AAY' : {'name': 'Allegiant Air', 'short_name':'Allegiant', 'image': 'allegiant-air.gif'},
    'AAL' : {'name': 'American Airlines', 'short_name':'American', 'image': 'american-airlines.jpg'},
    'EGF' : {'name': 'American Eagle Airlines', 'short_name':'American Eagle', 'image': 'american-eagle.png'},
    'ANA' : {'name': 'All Nippon Airways', 'short_name':'All Nippon', 'image': 'ana.jpg'},
    'AAR' : {'name': 'Asiana Airlines', 'short_name':'Asiana', 'image': 'asiana-airlines.png'},
    'AUA' : {'name': 'Austrian Airlines', 'short_name':'Austrian', 'image': 'austrian-airlines.gif'},
    'AVA' : {'name': 'Avianca - Aerovias Nacionales de Colombia, S.A.', 'short_name':'Avianca', 'image': 'avianca.png'},
    'AHY' : {'name': 'Azerbaijan Airlines', 'short_name':'Azerbaijan', 'image': 'azerbaijan-airlines.png'},
    'BKP' : {'name': 'Bangkok Airways', 'short_name':'Bangkok', 'image': 'bangkok-airways.png'},
    'BAW' : {'name': 'British Airways', 'short_name':'British', 'image': 'british-airways.jpg'},
    'BEL' : {'name': 'Brussels Airlines', 'short_name':'Brussels', 'image': 'brussels-airlines.jpg'},
    'CPA' : {'name': 'Cathay Pacific', 'short_name':'Cathay Pacific', 'image': 'cathay-pacific.jpg'},
    'CEB' : {'name': 'Cebu Pacific', 'short_name':'Cebu Pacific', 'image': 'cebu-pacific.png'},
    'CAL' : {'name': 'China Airlines', 'short_name':'China', 'image': 'china-airlines.jpg'},
    'CES' : {'name': 'China Eastern Airlines', 'short_name':'China Eastern', 'image': 'china-eastern.jpg'},
    'CSN' : {'name': 'China Southern Airlines', 'short_name':'China Southern', 'image': 'china-southern.jpg'},
    'CIB' : {'name': 'Condor', 'short_name':'Condor', 'image': 'condor.jpg'},
    'CMP' : {'name': 'Copa Airlines', 'short_name':'Copa', 'image': 'copa-airlines.jpg'},
    'CTN' : {'name': 'Croatia Airlines', 'short_name':'Croatia', 'image': 'croatia-airlines.gif'},
    'DAL' : {'name': 'Delta Air Lines', 'short_name':'Delta', 'image': 'delta.jpg'},
    'HDA' : {'name': 'Dragonair, Hong Kong Dragon Airlines', 'short_name':'Dragonair', 'image': 'dragon-air.jpg'},
    'EZY' : {'name': 'easyJet', 'short_name':'easyJet', 'image': 'easyjet.gif'},
    'UAE' : {'name': 'Emirates Airline', 'short_name':'Emirates', 'image': 'emirates.gif'},
    'ETH' : {'name': 'Ethiopian Airlines', 'short_name':'Ethiopian', 'image': 'ethiopian.gif'},
    'ETD' : {'name': 'Etihad Airways', 'short_name':'Etihad', 'image': 'etihad-airways.jpg'},
    'EVA' : {'name': 'EVA Air', 'short_name':'EVA Air', 'image': 'eva-air.jpg'},
    'FJI' : {'name': 'Fiji Airways', 'short_name':'Fiji', 'image': 'fiji-airways.jpg'},
    'FIN' : {'name': 'Finnair', 'short_name':'Finnair', 'image': 'finnair.png'},
    'FFT' : {'name': 'Frontier Airlines', 'short_name':'Frontier', 'image': 'frontier.gif'},
    'GIA' : {'name': 'Garuda Indonesia', 'short_name':'Garuda Indonesia', 'image': 'garuda-indonesia.png'},
    'GLO' : {'name': 'Gol Transportes Aereos', 'short_name':'Gol Transportes Aereos', 'image': 'gol.jpg'},
    'GFA' : {'name': 'Gulf Air', 'short_name':'Gulf Air', 'image': 'gulf-air.jpg'},
    'HAL' : {'name': 'Hawaiian Airlines', 'short_name':'Hawaiian', 'image': 'hawaiian-airlines.png'},
    'IBE' : {'name': 'Iberia Airlines', 'short_name':'Iberia', 'image': 'iberia.png'},
    'ICE' : {'name': 'Icelandair', 'short_name':'Icelandair', 'image': 'icelandair.jpg'},
    'IBU' : {'name': 'Indigo', 'short_name':'Indigo', 'image': 'indigo.jpg'},
    'JAL' : {'name': 'Japan Airlines', 'short_name':'Japan', 'image': 'japan-airlines.png'},
    'JBU' : {'name': 'JetBlue Airways', 'short_name':'JetBlue', 'image': 'jetblue.jpg'},
    'JST' : {'name': 'Jetstar Airways', 'short_name':'Jetstar', 'image': 'jetstar.png'},
    'KQA' : {'name': 'Kenya Airways', 'short_name':'Kenya', 'image': 'kenya-airways.jpg'},
    'KFR' : {'name': 'Kingfisher Airlines', 'short_name':'Kingfisher', 'image': 'kingfisher-airlines.jpg'},
    'KLM' : {'name': 'KLM', 'short_name':'KLM', 'image': 'klm.jpg'},
    'KAL' : {'name': 'Korean Air', 'short_name':'Korean Air', 'image': 'korean-air.gif'},
    'LAN' : {'name': 'LAN Airlines', 'short_name':'LAN', 'image': 'lan.jpg'},
    'LOT' : {'name': 'LOT Polish Airlines', 'short_name':'LOT', 'image': 'lot.gif'},
    'DLH' : {'name': 'Lufthansa', 'short_name':'Lufthansa', 'image': 'lufthansa.gif'},
    'MAS' : {'name': 'Malaysia Airlines', 'short_name':'Malaysia', 'image': 'malaysia.gif'},
    'MXA' : {'name': 'Mexicana de Aviacion', 'short_name':'Mexicana de Aviacion', 'image': 'mexicana.jpg'},
    'NAX' : {'name': 'Norwegian Air Shuttle', 'short_name':'Norwegian', 'image': 'norwegian.jpg'},
    'POE' : {'name': 'Porter Airlines', 'short_name':'Porter', 'image': 'porter.jpg'},
    'QFA' : {'name': 'Qantas', 'short_name':'Qantas', 'image': 'qantas.gif'},
    'QTR' : {'name': 'Qatar Airways', 'short_name':'Qatar', 'image': 'qatar-airways.jpg'},
    'RYR' : {'name': 'Ryanair', 'short_name':'Ryanair', 'image': 'ryanair.jpg'},
    'SVA' : {'name': 'Saudia', 'short_name':'Saudia', 'image': 'saudi-airlines.png'},
    'SAS' : {'name': 'Scandinavian Airlines', 'short_name':'Scandinavian', 'image': 'scandinavian-airlines.jpg'},
    'CSZ' : {'name': 'Shenzhen Airlines', 'short_name':'Shenzhen', 'image': 'shenzhen-airlines.jpg'},
    'SLK' : {'name': 'SilkAir', 'short_name':'SilkAir', 'image': 'silkair.png'},
    'SIA' : {'name': 'Singapore Airlines', 'short_name':'Singapore', 'image': 'singapore-airlines.jpg'},
    'SKW' : {'name': 'SkyWest Airlines', 'short_name':'SkyWest', 'image': 'skywest-airlines.png'},
    'SAA' : {'name': 'South African Airways', 'short_name':'South African', 'image': 'south-african-airways.png'},
    'SWA' : {'name': 'Southwest Airlines', 'short_name':'Southwest', 'image': 'southwest.jpg'},
    'NKS' : {'name': 'Spirit Airlines', 'short_name':'Spirit', 'image': 'spirit-airlines.jpg'},
    'ALK' : {'name': 'SriLankan Airlines', 'short_name':'SriLankan', 'image': 'srilankan-airlines.gif'},
    'SWR' : {'name': 'Swissair', 'short_name':'Swissair', 'image': 'swissair.jpg'},
    'TAT' : {'name': 'Grupo TACA', 'short_name':'Grupo TACA', 'image': 'taca.gif'},
    'TAM' : {'name': 'TAM Brazilian Airlines', 'short_name':'TAM Brazilian', 'image': 'tam.gif'},
    'TAP' : {'name': 'TAP Portugal', 'short_name':'TAP Portugal', 'image': 'tap.gif'},
    'ROT' : {'name': 'Tarom', 'short_name':'Tarom', 'image': 'tarom.gif'},
    'THA' : {'name': 'Thai Airways International', 'short_name':'Thai', 'image': 'thai-airways.jpg'},
    'TOM' : {'name': 'Thomson Airways', 'short_name':'Thomson', 'image': 'thomson-airways.jpg'},
    'TSO' : {'name': 'Transaero Airlines', 'short_name':'Transaero', 'image': 'transaero-airlines.png'},
    'THY' : {'name': 'Turkish Airlines', 'short_name':'Turkish', 'image': 'turkish-airlines.gif'},
    'UAL' : {'name': 'United Airlines', 'short_name':'United', 'image': 'united-airlines.png'},
    'AWE' : {'name': 'US Airways', 'short_name':'US Airways', 'image': 'us-airways.jpg'},
    'VRD' : {'name': 'Virgin America', 'short_name':'Virgin', 'image': 'virgin-america.jpg'},
    'VOI' : {'name': 'Volaris', 'short_name':'Volaris', 'image': 'volaris.png'},
    'VLG' : {'name': 'Vueling Airlines', 'short_name':'Veuling', 'image': 'vueling.png'},
    'WJA' : {'name': 'WestJet', 'short_name':'WestJet', 'image': 'west-jet.png'},
    'WZZ' : {'name': 'Wizz Air', 'short_name':'Wizz Air', 'image': 'wizz-air.jpg'},
  }

  matches = [ {'image': i['image'], 'short_name': i['short_name']} for i in airlines.itervalues() if i['name'].lower() in name.lower() ]

  if len(matches) == 1:
    return matches[0]
  else:
    return None

if __name__ == "__main__":

    print get_airline_info('Wizz Air')
