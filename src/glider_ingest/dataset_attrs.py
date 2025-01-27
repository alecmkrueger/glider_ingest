from glider_ingest.variable import Variable

# Flight Variables

m_pressure = Variable(
    data_source_name='m_pressure',
    short_name='m_pressure',
    accuracy=0.01,
    ancillary_variables='',
    axis='Z',
    bytes=4,
    comment='Alias for m_pressure',
    long_name='GPS Pressure',
    observation_type='measured',
    platform='platform',
    positive='down',
    precision=0.01,
    reference_datum='sea-surface',
    resolution=0.01,
    source_sensor='sci_water_pressure',
    standard_name='sea_water_pressure',
    units='bar',
    valid_max=2000.0,
    valid_min=0.0,
)

m_water_depth = Variable(
    data_source_name='m_water_depth',
    short_name='depth',
    accuracy=0.01,
    ancillary_variables='',
    axis='Z',
    bytes=4,
    comment='Alias for m_depth',
    long_name='GPS Depth',
    observation_type='calculated',
    platform='platform',
    positive='down',
    precision=0.01,
    reference_datum='sea-surface',
    resolution=0.01,
    source_sensor='m_depth',
    standard_name='sea_water_depth',
    units='meters',
    valid_max=2000.0,
    valid_min=0.0,
)

m_latitude = Variable(
    data_source_name='m_lat',
    short_name='latitude',
    ancillary_variables='',
    axis='Y',
    bytes=8,
    comment='m_gps_lat converted to decimal degrees and interpolated',
    coordinate_reference_frame='urn:ogc:crs:EPSG::4326',
    long_name='Latitude',
    observation_type='calculated',
    platform='platform',
    precision=5,
    reference_datum='WGS84',
    source_sensor='m_gps_lat',
    standard_name='latitude',
    units='degree_north',
    valid_max=90.0,
    valid_min=-90.0,
)

m_longitude = Variable(
    data_source_name='m_lon',
    short_name='longitude',
    ancillary_variables='',
    axis='X',
    bytes=8,
    comment='m_gps_lon converted to decimal degrees and interpolated',
    coordinate_reference_frame='urn:ogc:crs:EPSG::4326',
    long_name='Longitude',
    observation_type='calculated',
    platform='platform',
    precision=5,
    reference_datum='WGS84',
    source_sensor='m_gps_lon',
    standard_name='longitude',
    units='degree_east',
    valid_max=180.0,
    valid_min=-180.0,
)

# Science Variables

sci_water_pressure = Variable(
    data_source_name='sci_water_pressure',
    short_name='pressure',
    accuracy=0.01,
    ancillary_variables='',
    axis='Z',
    bytes=4,
    comment='Alias for sci_water_pressure',
    instrument='instrument_ctd',
    long_name='CTD Pressure',
    observation_type='measured',
    platform='platform',
    positive='down',
    precision=0.01,
    reference_datum='sea-surface',
    resolution=0.01,
    source_sensor='sci_water_pressure',
    standard_name='sea_water_pressure',
    units='bar',
    valid_max=2000.0,
    valid_min=0.0,
)

sci_water_temp = Variable(
    data_source_name='sci_water_temp',
    short_name='temperature',
    accuracy=0.004,
    ancillary_variables='',
    bytes=4,
    instrument='instrument_ctd',
    long_name='Temperature',
    observation_type='measured',
    platform='platform',
    precision=0.001,
    resolution=0.001,
    standard_name='sea_water_temperature',
    units='Celsius',
    valid_max=40.0,
    valid_min=-5.0,
    to_grid=True
)

sci_water_cond = Variable(
    data_source_name='sci_water_cond',
    short_name='conductivity',
    accuracy=0.001,
    ancillary_variables='',
    bytes=4,
    instrument='instrument_ctd',
    long_name='sci_water_cond',
    observation_type='measured',
    platform='platform',
    precision=1e-05,
    resolution=1e-05,
    standard_name='sea_water_electrical_conductivity',
    units='S m-1',
    valid_max=10.0,
    valid_min=0.0,
    to_grid=True
)

sci_water_sal = Variable(
    data_source_name='calculated_salinity',
    short_name='salinity',
    accuracy='',
    ancillary_variables='',
    instrument='instrument_ctd',
    long_name='Salinity',
    observation_type='calculated',
    platform='platform',
    precision='',
    resolution='',
    standard_name='sea_water_practical_salinity',
    units='1',
    valid_max=40.0,
    valid_min=0.0,
    to_grid=True
)

sci_water_dens = Variable(
    data_source_name='calculated_density',
    short_name='density',
    accuracy='',
    ancillary_variables='',
    instrument='instrument_ctd',
    long_name='Density',
    observation_type='calculated',
    platform='platform',
    precision='',
    resolution='',
    standard_name='sea_water_density',
    units='kg m-3',
    valid_max=1040.0,
    valid_min=1015.0,
    to_grid=True
)

sci_flbbcd_bb_units = Variable(
    data_source_name='sci_flbbcd_bb_units',
    short_name='turbidity',
    accuracy='',
    ancillary_variables='',
    instrument='instrument_flbbcd',
    long_name='Turbidity',
    observation_type='calculated',
    platform='platform',
    precision='',
    resolution='',
    standard_name='sea_water_turbidity',
    units='1',
    valid_max=1.0,
    valid_min=0.0,
    to_grid=True
)

sci_flbbcd_cdom_units = Variable(
    data_source_name='sci_flbbcd_cdom_units',
    short_name='cdom',
    accuracy='',
    ancillary_variables='',
    instrument='instrument_flbbcd',
    long_name='CDOM',
    observation_type='calculated',
    platform='platform',
    precision='',
    resolution='',
    standard_name='concentration_of_colored_dissolved_organic_matter_in_sea_water',
    units='ppb',
    valid_max=50.0,
    valid_min=0.0,
    to_grid=True
)

sci_flbbcd_chlor_units = Variable(
    data_source_name='sci_flbbcd_chlor_units',
    short_name='chlorophyll',
    accuracy='',
    ancillary_variables='',
    instrument='instrument_flbbcd',
    long_name='Chlorophyll_a',
    observation_type='calculated',
    platform='platform',
    precision='',
    resolution='',
    standard_name='mass_concentration_of_chlorophyll_a_in_sea_water',
    units='\u03BCg/L',
    valid_max=10.0,
    valid_min=0.0,
    to_grid=True
)

sci_oxy4_oxygen = Variable(
    data_source_name='sci_oxy4_oxygen',
    short_name='oxygen',
    accuracy='',
    ancillary_variables='',
    instrument='instrument_ctd_modular_do_sensor',
    long_name='oxygen',
    observation_type='calculated',
    platform='platform',
    precision='',
    resolution='',
    standard_name='moles_of_oxygen_per_unit_mass_in_sea_water',
    units='\u03BCmol/kg',
    valid_max=500.0,
    valid_min=0.0,
    to_grid=True
)
