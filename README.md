<a id="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/alecmkrueger/glider-ingest">
    <img src="https://github.com/alecmkrueger/glider_ingest/blob/99e983da8ed0793bda3c7aa53cb7b4f133a07ad9/.github/TAMU-GERG-Glider.jpg?raw=true" alt="Logo" width="500" height="272">
  </a>

<h3 align="center">GERG Glider Ingest</h3>

  <p align="center">
    Convert raw data from GERG gliders into netcdf using python
    <br />
    <a href="https://glider-ingest.readthedocs.io/en/latest/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/alecmkrueger/glider-ingest/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/alecmkrueger/glider-ingest/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#dependencies">Dependencies</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

This project was created to streamline the process of converting the raw data from the gliders after missions into NetCDF files, 
as well as ensuring the code can be easily maintained, understood, and used by others.



### Built With

[![Python][Python]][Python-url]



<!-- GETTING STARTED -->
## Getting Started

There are three ways to get started
1. Create a fresh virtual environment using your favorite method and install the dependencies
2. Use an already established virtual environment and install the dependencies



### Dependencies
I have provided some commands to install the dependencies using conda but you can use any package manager

1. #### Creating your own virtual environment then installing dependencies
    You can change "glider_ingest" to your desired environment name 

    ```sh
    conda create -n glider_ingest python=3.12
    ```
    
    ```sh
    conda activate glider_ingest
    ```

    ```sh
    pip install numpy pandas xarray gsw attrs
    ```

2. #### Using an already established virtual environment

    ```sh
    conda activate your_env
    ```

    ```sh
    pip install numpy pandas xarray gsw attrs
    ```

### Installation

1. Activate your virtual environment
1. Verify/Install Dependencies
1. Clone the repo
   ```sh
   git clone https://github.com/alecmkrueger/glider-ingest.git
   ```





<!-- USAGE EXAMPLES -->
## Usage

Process raw data from gliders using python. 

Function inputs:
* raw_data_source (Path|str): Raw data source, from the glider SD card
* working_directory (Path|str): Where you want the raw copy and processed data to be
* glider_number (str): The number of the glider, for NetCDF metadata
* mission_title (str): The mission title, for NetCDF metadata
* extensions (list): The extensions you wish to process
* output_nc_filename (str): The name of the output NetCDF file
* return_ds (bool): If you would like the output dataset to be returned. Default = False

Example:

```sh
from pathlib import Path

from glider_ingest import MissionData, MissionProcessor

memory_card_copy_loc = Path('path/to/memory/card/copy')
# Where you want the netcdf to be saved to
working_dir = Path('path/to/working/dir').resolve()
mission_num = '46'

# Initalize the mission_data container
mission_data = MissionData(memory_card_copy_loc=memory_card_copy_loc,
                         working_dir=working_dir,
                         mission_num=mission_num)
# Pass the mission_data container to the MissionProcessor class
# call save_mission_dataset to generate and save the mission dataset
MissionProcessor(mission_data=mission_data).save_mission_dataset()
```




<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request





<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Alec Krueger - alecmkrueger@tamu.edu

Project Link: [https://github.com/alecmkrueger/glider-ingest](https://github.com/alecmkrueger/glider-ingest)



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* Sakib Mahmud, Texas A&M University, Geochemical and Environmental Research Group, sakib@tamu.edu
* Xiao Ge, Texas A&M University, Geochemical and Environmental Research Group, gexiao@tamu.edu
* Alec Krueger, Texas A&M University, Geochemical and Environmental Research Group, alecmkrueger@tamu.edu

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/alecmkrueger/glider-ingest.svg?style=for-the-badge
[contributors-url]: https://github.com/alecmkrueger/glider-ingest/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/alecmkrueger/glider-ingest.svg?style=for-the-badge
[forks-url]: https://github.com/alecmkrueger/glider-ingest/network/members
[stars-shield]: https://img.shields.io/github/stars/alecmkrueger/glider-ingest.svg?style=for-the-badge
[stars-url]: https://github.com/alecmkrueger/glider-ingest/stargazers
[issues-shield]: https://img.shields.io/github/issues/alecmkrueger/glider-ingest.svg?style=for-the-badge
[issues-url]: https://github.com/alecmkrueger/glider-ingest/issues
[license-shield]: https://img.shields.io/github/license/alecmkrueger/glider-ingest.svg?style=for-the-badge
[license-url]: https://github.com/alecmkrueger/glider-ingest/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/aleckrueger
[product-screenshot]: images/screenshot.png
[Python]: https://img.shields.io/badge/python-000000?&logo=python
[Python-url]: https://www.python.org/
