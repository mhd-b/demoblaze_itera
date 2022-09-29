An example project for end-to-end GUI automated testing on online store "https://www.demoblaze.com/". 

The project is written in python, using Pytest as testing framework, Selenium webdriver for automating GUI, <br> assertpy as assertion library, and Allure for rich HTML test reports.

<h3> Installation </h3>
- Clone repo & Install dependencies <br>
<code> pip install -r requirements.txt</code> <br>
- Install Allure command line for generating HTML reports, for linux: <br>
<code>sudo apt-add-repository ppa:qameta/allure <br>
sudo apt-get update  <br>
sudo apt-get install allure </code>
<br> <br><b>For windows or Mac refer to documentation:</b><br>
<link> https://docs.qameta.io/allure-report/#_installing_a_commandline

<h3> running tests </h3>
<br>Running tests and generate results as allure json files 
<code> pytest main.py --alluredir=./allure_results </code>
<h4> Generate and open HTML report based on JSON test results</h4>
<code> allure serve ./allure_results </code>
<br><br> Else run the main.py file from Pycharm or any python enabled IDEA.<br>

Example of HTML reports can be found here <link> 