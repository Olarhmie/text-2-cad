import trimesh
from simple_mesh import generate_simple_mesh
import gmsh
from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
from PIL import Image, ImageDraw, ImageFont
import os
from openscad_runner import RenderMode, OpenScadRunner
from openai import OpenAI
from dotenv import load_dotenv
import re

from llama_index.storage.storage_context import StorageContext
from llama_index.indices.loading import load_index_from_storage

import chromadb
from llama_index.vector_stores import ChromaVectorStore
from datetime import datetime
import json
import subprocess  #added this
import uuid

with open("../keys.json", "r") as f:
    keys = json.load(f)
OPENAI_API_KEY = keys["openai"]

load_dotenv()  # take environment variables from .env.

client = OpenAI(
    api_key=os.getenv('OPENAI_AI_KEY')
)
            
          



def get_query_engine():
    # rebuild storage context
    storage_context = StorageContext.from_defaults(persist_dir="index")

    # load index
    index = load_index_from_storage(storage_context)

    # initialize client, setting path to save data
    db = chromadb.PersistentClient(path="./chroma_db")

    # create collection
    chroma_collection = db.get_or_create_collection("quickstart")

    # assign chroma as the vector_store to the context
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # create a query engine and query
    query_engine = index.as_query_engine()
    return query_engine


query_engine = get_query_engine()


system_prompt = "Let's suppose fictionally that you are an expert in CAD design and coding in OpenSCAD scripting language.\n"

def query(request, toggleRag):
    prompt = f"Create the OpenSCAD code to generate the 3D model for a {request}. Answer ONLY with the code, no comments or explanations.\n"
    if toggleRag == "on":
        # for rag:
        answ = query_engine.query(prompt)
        return answ.response
    else:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
            )
        
        answ = response.choices[0].message.content
        return answ
    

    

app = Flask(__name__)


   


@app.route('/')
def index():
    return render_template('index.html')

#added this for the mesh visualization
@app.route('/view_mesh/<filename>')
def view_mesh(filename):
    """Render an interactive 3D viewer for the mesh"""
    return render_template('mesh_viewer.html', filename=filename)

@app.route('/submit', methods=['POST'])
def submit():
    text = request.form['text']
    toggleRag = request.form['toggleRag']
    
    answer = query(text, toggleRag)
    print(answer)

    if "```" in answer:
        answer = answer.split("```")[1]
    elif "`" in answer:
        answer = answer.split("`")[1]



    answer = re.sub(r'openscad', '', answer, flags=re.IGNORECASE)

    # save the scad file with the timestamp as the filename
    curr_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    scad_path = os.path.join("scad_scripts", curr_timestamp + ".scad")
    stl_output_path = os.path.join("static", "stl", curr_timestamp + ".stl")
    
    
    

    # save a scad file with the answer
    os.makedirs(os.path.dirname(scad_path), exist_ok=True)
    # ensure the static/images directory exists for output images
    os.makedirs(os.path.join("static", "images"), exist_ok=True)
    # ensure the STL format output exist
    os.makedirs(os.path.join("static", "stl"), exist_ok=True)
    os.makedirs(os.path.join("static", "mesh"), exist_ok=True)
    

    

    


    with open(scad_path, 'w') as f:
        f.write(answer)

    

  

    try:
        print("Generating STL...")
        print("Command:", ["openscad", "-o", stl_output_path, scad_path])
    
        result = subprocess.run(
        ["openscad", "-o", stl_output_path, scad_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True)
    

        print("STDOUT:", result.stdout.decode())
        print("STDERR:", result.stderr.decode())
        print("✅ STL file created at:", stl_output_path)
    except subprocess.CalledProcessError as e:
        print("❌ Error generating STL:", e)
        print("STDERR:", e.stderr.decode())

    #mesh generation 
    print("Generating simplified mesh...")
    msh_output_path = os.path.join("static", "mesh", curr_timestamp + ".ply")
    mesh_path = generate_simple_mesh(stl_output_path, msh_output_path)

    if not mesh_path or not os.path.exists(msh_output_path):
        print("❌ Mesh generation failed")

    
   


   
            
        
    

        
    # render the scad file
    # png
    osr = OpenScadRunner(scad_path, f"static/images/{curr_timestamp}.png", render_mode=RenderMode.preview, imgsize=(800,600))


    print(curr_timestamp)
    print(scad_path)

    # gif
    # osr = OpenScadRunner(filename + ".scad", f"static/images/{filename}.gif", imgsize=(320,200), animate=36, animate_duration=200)


    osr.run()
    

    if osr.good():
        return jsonify({'image': f"{curr_timestamp}.png", 'filename': curr_timestamp, 'stl': f"{curr_timestamp}.stl", 'msh': f"{curr_timestamp}.ply", 'view_url': f"/view_mesh/{curr_timestamp}"})
    else:
        # Fallback generic message; OpenScadRunner may not expose an error attribute
        return jsonify({'error': 'OpenSCAD rendering failed.'})



@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Send the requested SCAD file to the user."""
    directory = os.path.join(app.root_path, 'scad_scripts')
    print(directory)
    print(filename)
    return send_from_directory(directory, filename + ".scad", as_attachment=True)



#route to download STL
@app.route('/download_stl/<filename>', methods=['GET'])
def download_stl(filename):
    return send_from_directory('static/stl', filename + ".stl", as_attachment=True)

@app.route('/download_mesh/<filename>', methods=['GET'])
def download_mesh(filename):
    """Serve the generated PLY mesh file"""
    return send_from_directory(
        'static/mesh',
        f"{filename}.ply",
        as_attachment=True,
        mimetype='application/octet-stream'
    )



if __name__ == '__main__':
    app.run(debug=False, threaded=True)

