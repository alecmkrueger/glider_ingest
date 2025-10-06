glider_ingest.variable
======================

.. py:module:: glider_ingest.variable


Classes
-------

.. autoapisummary::

   glider_ingest.variable.Variable


Module Contents
---------------

.. py:class:: Variable

   A class to represent a variable in a glider mission dataset.


   .. py:method:: to_dict()

      Convert the Variable object to a dictionary, sorted by key and filtered out None values.



   .. py:attribute:: accuracy
      :type:  float | None


   .. py:attribute:: ancillary_variables
      :type:  str | None


   .. py:attribute:: axis
      :type:  str | None


   .. py:attribute:: bytes
      :type:  str | None | int


   .. py:property:: calculated
      :type: bool



   .. py:attribute:: comment
      :type:  str | None


   .. py:attribute:: coordinate_reference_frame
      :type:  str | None


   .. py:attribute:: data_source_name
      :type:  str | None


   .. py:attribute:: id
      :type:  str | None


   .. py:attribute:: instrument
      :type:  str | None


   .. py:attribute:: instruments
      :type:  str | None


   .. py:property:: long_name
      :type: str | None



   .. py:attribute:: observation_type
      :type:  str | None


   .. py:attribute:: platform
      :type:  str | None


   .. py:attribute:: positive
      :type:  str | None


   .. py:attribute:: precision
      :type:  str | None | float


   .. py:attribute:: reference_datum
      :type:  str | None


   .. py:attribute:: resolution
      :type:  str | None | float


   .. py:property:: short_name
      :type: str | None



   .. py:attribute:: source
      :type:  str | None


   .. py:attribute:: source_sensor
      :type:  str | None


   .. py:attribute:: standard_name
      :type:  str | None


   .. py:attribute:: to_grid
      :type:  bool | str


   .. py:attribute:: type
      :type:  str | None


   .. py:attribute:: units
      :type:  str | None


   .. py:property:: update_time
      :type: str



   .. py:attribute:: valid_max
      :type:  str | None | float


   .. py:attribute:: valid_min
      :type:  str | None | float


   .. py:property:: wmo_id
      :type: str | None



