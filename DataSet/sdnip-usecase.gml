graph [
  DateType "Random"
  Backbone 1
  Customer 0
  IX 0
  Layer "IP"
  Creator "babu"
  Developed 0
  Transit 0
  NetworkDate "2020_06"
  DateYear "2020"
  LastProcessed "2020_06_01"
  Testbed 0
  node [
    id 4
    label "S1"
    Country "AS0"
    Longitude -112.24368
    Internal 1
    Latitude 29.05223
  ]
  node [
    id 5
    label "S2"
    Country "AS0"
    Longitude -118.24368
    Internal 1
    Latitude 34.05223
  ]
  node [
    id 6
    label "S3"
    Country "AS0"
    Longitude -104.9847
    Internal 1
    Latitude 39.73915
  ]
  node [
    id 7
    label "S4"
    Country "AS0"
    Longitude -94.62746
    Internal 1
    Latitude 39.11417
  ]
  node [
    id 8
    label "S5"
    Country "AS0"
    Longitude -95.36327
    Internal 1
    Latitude 29.76328
  ]
  node [
    id 9
    label "S6"
    Country "AS0"
    Longitude -84.38798
    Internal 1
    Latitude 33.749
  ]
  
  edge [
    source 4
    target 6
    weight 10.0
  ]
  edge [
    source 4
    target 8
    weight 7.0
  ]
  edge [
    source 8
    target 9
    weight 6.0
  ]
  edge [
    source 6
    target 9
    weight 10.0
  ]
  edge [
    source 8
    target 5
    weight 10.0
  ]
  edge [
    source 5
    target 7
    weight 10.0
  ]
  edge [
    source 7
    target 9
    weight 10.0
  ]
]
