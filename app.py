
import json

import src.tests.testconfig as tc

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

from src.parsedata import PDFParser
from src.capitalgains import CapitalGains
from src.initialize import Logger



app = Flask(__name__, template_folder='templates')

# To avoid below error  duringg local Testing
# Access to fetch ' from origin ' has been blocked by CORS policy
CORS(app)

#Only for testing: Using seperate FE
@app.route('/')
def get_data_for_test():
    logger = Logger()
    logger.initilaze_logging('no')    

    dp = PDFParser()

    mf_trans_df, mf_hdr_df = dp.parse_mf_data('cas.pdf', tc.password)
    target_ltcg = 100000
    cg = CapitalGains(mf_hdr_df, mf_trans_df)
    cg.prepare_final_data(target_ltcg)

    hdr_df = cg.output_hdr_df  
    # trans_df = cg.mf_trans_df

    hdr_json = hdr_df.to_json(orient="records")
    parsed = json.loads( hdr_json )
    response = json.dumps(parsed, indent=4)
    # response = jsonify( hdr_df )
    #  so that lcoal testing can be done 
    # response.headers.add("Access-Control-Allow-Origin", "*")  
    return response


@app.route('/upload', methods = ['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename('cas.pdf')) 

        logger = Logger()
        logger.initilaze_logging('no')     

        dp = PDFParser()
        mf_trans_df, mf_hdr_df = dp.parse_mf_data('cas.pdf', tc.password)
        target_ltcg = 100000
        cg = CapitalGains(mf_hdr_df, mf_trans_df)
        cg.prepare_final_data(target_ltcg)

        hdr_df = cg.output_hdr_df  
        # trans_df = cg.mf_trans_df

        hdr_json = hdr_df.to_json(orient="records")
        parsed = json.loads( hdr_json )
        response = json.dumps(parsed, indent=4)
        return response

@app.route("/transdata")
def get_trans_data():
    logger = Logger()
    logger.initilaze_logging('no')     

    dp = PDFParser()
    mf_trans_df, mf_hdr_df = dp.parse_mf_data('cas.pdf', tc.password)
    target_ltcg = 100000
    cg = CapitalGains(mf_hdr_df, mf_trans_df)
    cg.prepare_final_data(target_ltcg)

    trans_df = cg.mf_trans_df
    trans_json = trans_df.to_json(orient="records")
    parsed = json.loads( trans_json )
    response = json.dumps(parsed, indent=4)
    return response


if __name__ == '__main__':
   app.run(debug = True)
		