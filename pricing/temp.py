def return_search_res():

  flights = [
              {
              'fare': 500,
              'cabin': 'coach',
              'deeplink': 'suckmyballs.com',
              'departing': {
                            'airline': 'Delta',
                            'airline_image': 'suckmyballs.com/static/airlines/delta',
                            'take_off_airport_code': 'SFO',
                            'landing_airport_code': 'JFK',
                            'take_off_date': '2013-4-5',
                            'take_off_date_timestamp': '1382162766000',
                            'take_off_time': 1200,
                            'landing_date': '2013-4-5',
                            'landing_date_timestamp': '1382162766000',
                            'landing_time': 1500,
                            'number_stops': 1,
                            'trip_duration': 180,
                            'detail': [
                                        {
                                        'airline': 'Delta',
                                        'take_off_airport_code': 'SFO',
                                        'take_off_city': 'San Francisco',
                                        'landing_airport_code': 'DEN',
                                        'take_off_city': 'Denver',
                                        'flight_number': '1232',
                                        'take_off_date': '2013-4-5',
                                        'take_off_date_timestamp': '1382162766000',
                                        'take_off_time': 1200,
                                        'landing_date': '2013-4-5',
                                        'landing_date_timestamp': '1382162766000',
                                        'landing_time': 1300,
                                        'trip_duration': 60,
                                        },
                                        {
                                        'airline': 'Delta',
                                        'flight_number': '109',
                                        'take_off_airport_code': 'DEN',
                                        'take_off_city': 'Denver',
                                        'landing_airport_code': 'JFK',
                                        'take_off_city': 'New York City',
                                        'take_off_date': '2013-4-5',
                                        'take_off_date_timestamp': '1382162766000',
                                        'take_off_time': 1400,
                                        'landing_date': '2013-4-5',
                                        'landing_date_timestamp': '1382162766000',
                                        'landing_time': 1500,
                                        'trip_duration': 60,
                                        },
                                      ]
                            },
              'returning': {
                            'airline': 'KLM',
                            'airline_image': 'suckmyballs.com/static/airlines/klm',
                            'take_off_airport_code': 'JFK',
                            'landing_airport_code': 'SFO',
                            'take_off_date': '2013-4-10',
                            'take_off_date_timestamp': '1382162766000',
                            'take_off_time': 600,
                            'landing_date': '2013-4-10',
                            'landing_date_timestamp': '1382162766000',
                            'landing_time': 900,
                            'number_stops': 0,
                            'trip_duration': 180,
                            'detail': [
                                        {
                                        'airline': 'KLM',
                                        'flight_number': 'A2',
                                        'take_off_airport_code': 'JFK',
                                        'take_off_city': 'New York City',
                                        'landing_airport_code': 'SFO',
                                        'take_off_city': 'San Francisco',
                                        'take_off_date': '2013-4-5',
                                        'take_off_date_timestamp': '1382162766000',
                                        'take_off_time': 600,
                                        'landing_date': '2013-4-5',
                                        'landing_date_timestamp': '1382162766000',
                                        'landing_time': 900,
                                        'trip_duration': 180,
                                        },
                                      ]
                            },
              },

            ]

  return flights