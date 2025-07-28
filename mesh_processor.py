from flask import Flask, request, jsonify
import os
import trimesh
import meshio

try:
    import tetgen
    TETGEN_AVAILABLE = True
except ImportError:
    TETGEN_AVAILABLE = False

app = Flask(__name__)

def generate_mesh_from_stl(
    stl_path,
    msh_output_path=None,
    volume_mesh=False,
    mesh_format="msh"
):
    if not os.path.exists(stl_path):
        raise FileNotFoundError(f"STL file not found: {stl_path}")

    if msh_output_path is None:
        msh_output_path = stl_path.replace(".stl", f".{mesh_format}")

    mesh = trimesh.load_mesh(stl_path)

    if volume_mesh:
        if not TETGEN_AVAILABLE:
            raise ImportError("TetGen not installed. Run: pip install tetgen")

        points = mesh.vertices
        faces = mesh.faces
        tgen = tetgen.TetGen(points, faces)
        tmesh = tgen.tetrahedralize(order=1, mindihedral=20, minratio=1.5)

        meshio.write_points_cells(
            msh_output_path,
            tmesh.points,
            {"tetra": tmesh.cells},
        )
    else:
        temp_ply = msh_output_path.replace(f".{mesh_format}", ".ply")
        mesh.export(temp_ply)

        mesh_data = meshio.read(temp_ply)
        meshio.write(msh_output_path, mesh_data)

    return msh_output_path


@app.route("/generate_mesh", methods=["POST"])
def generate_mesh_endpoint():
    """
    Request JSON example:
    {
        "stl_path": "static/stl/model.stl",
        "volume_mesh": false,
        "mesh_format": "msh"
    }
    """
    data = request.json
    stl_path = data.get("stl_path")
    volume_mesh = data.get("volume_mesh", False)
    mesh_format = data.get("mesh_format", "msh")

    if not stl_path:
        return jsonify({"error": "Missing 'stl_path' in request"}), 400

    try:
        output_path = generate_mesh_from_stl(
            stl_path,
            msh_output_path=None,
            volume_mesh=volume_mesh,
            mesh_format=mesh_format
        )
        return jsonify({"message": "Mesh generated successfully", "mesh_file": output_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5050)
