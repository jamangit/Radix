import sys

from wordmeter_api.local import main

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        from wordmeter_api.selftest import run

        run()
    else:
        main()
