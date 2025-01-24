from glider_ingest.utils import timing

import time

# Add the timing decorator to the main function
@timing
def main():
    """
    Example of how to use the timing decorator.
    """   
    # Wait for 2 seconds
    time.sleep(2)
    

if __name__ == '__main__':
    main()
