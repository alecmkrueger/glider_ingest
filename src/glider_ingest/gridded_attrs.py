from glider_ingest.variable import Variable

def generate_variables(interval_h, interval_p):
    g_temperature = Variable(
        long_name='Gridded Temperature',
        short_name='g_temperature',
        observation_type='calculated',
        source='temperature from sci_water_temp',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='sea_water_temperature',
        units='Celsius',
        valid_max=40.0,
        valid_min=-5.0
    )

    g_salinity = Variable(
        long_name='Gridded Salinity',
        short_name='g_salinity',
        observation_type='calculated',
        source='salinity from sci_water_sal',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='sea_water_practical_salinity',
        units='1',
        valid_max=40.0,
        valid_min=0.0
    )

    g_conductivity = Variable(
        long_name='Gridded Conductivity',
        short_name='g_conductivity',
        observation_type='calculated',
        source='conductivity from sci_water_cond',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='sea_water_electrical_conductivity',
        units='S m-1',
        valid_max=10.0,
        valid_min=0.0
    )

    g_density = Variable(
        long_name='Gridded Density',
        short_name='g_density',
        observation_type='calculated',
        source='density from sci_water_dens',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='sea_water_density',
        units='kg m-3',
        valid_max=1040.0,
        valid_min=1015.0
    )

    g_turbidity = Variable(
        long_name='Gridded Turbidity',
        short_name='g_turbidity',
        observation_type='calculated',
        source='turbidity from sci_flbbcd_bb_units',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='sea_water_turbidity',
        units='1',
        valid_max=1.0,
        valid_min=0.0
    )

    g_cdom = Variable(
        long_name='Gridded CDOM',
        short_name='g_cdom',
        observation_type='calculated',
        source='cdom from sci_flbbcd_cdom_units',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='concentration_of_colored_dissolved_organic_matter_in_sea_water',
        units='ppb',
        valid_max=50.0,
        valid_min=0.0
    )

    g_chlorophyll = Variable(
        long_name='Gridded Chlorophyll_a',
        short_name='g_chlorophyll',
        observation_type='calculated',
        source='chlorophyll from sci_flbbcd_chlor_units',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='mass_concentration_of_chlorophyll_a_in_sea_water',
        units='\u03BCg/L',
        valid_max=10.0,
        valid_min=0.0
    )

    g_oxygen = Variable(
        long_name='Gridded Oxygen',
        short_name='g_oxygen',
        observation_type='calculated',
        source='oxygen from sci_oxy4_oxygen',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='moles_of_oxygen_per_unit_mass_in_sea_water',
        units='\u03BCmol/kg',
        valid_max=500.0,
        valid_min=0.0
    )

    g_hc = Variable(
        long_name='Gridded Heat Content',
        short_name='g_hc',
        observation_type='calculated',
        source='g_temp',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='sea_water_heat_content_for_all_grids',
        units='kJ/cm^2',
        valid_max=10.0,
        valid_min=0.0
    )

    g_phc = Variable(
        long_name='Gridded Potential Heat Content',
        short_name='g_phc',
        observation_type='calculated',
        source='g_temp',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='sea_water_heat_content_for_grids_above_26�C',
        units='kJ/cm^2',
        valid_max=10.0,
        valid_min=0.0
    )

    g_sp = Variable(
        long_name='Gridded Spiciness',
        short_name='g_sp',
        observation_type='calculated',
        source='g_temp',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='spiciness_from_absolute_salinity_and_conservative_temperature_at_0dbar',
        units='kg/m^3',
        valid_max=10.0,
        valid_min=0.0
    )

    g_depth = Variable(
        long_name='Gridded Depth',
        short_name='g_depth',
        observation_type='calculated',
        source='g_pres',
        resolution=str(interval_h)+'hour and '+str(interval_p)+'dbar',
        standard_name='sea_water_depth',
        units='m',
        valid_max=1000.0,
        valid_min=0.0
    )

    # Create a list of variables that we initilized above
    variables = [g_temperature, g_salinity, g_conductivity, g_density, g_turbidity, 
                 g_cdom, g_chlorophyll, g_oxygen, g_hc, g_phc, g_sp, g_depth]
    # Create a dictionary of variables that we initilized above
    attrs_dict = {value.short_name:value for value in variables} 
    return attrs_dict
