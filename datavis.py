import open3d as o3d
import numpy as np
import copy

def print_separator(step_number, step_name):
    """Print a nice separator for each step"""
    print("\n" + "="*80)
    print(f"STEP {step_number}: {step_name}")
    print("="*80)

def print_mesh_info(mesh, step_name=""):
    """Print information about a mesh"""
    print(f"\n--- {step_name} Information ---")
    print(f"Number of vertices: {len(mesh.vertices)}")
    print(f"Number of triangles: {len(mesh.triangles)}")
    print(f"Has vertex colors: {mesh.has_vertex_colors()}")
    print(f"Has vertex normals: {mesh.has_vertex_normals()}")
    print(f"Has triangle normals: {mesh.has_triangle_normals()}")

def print_point_cloud_info(pcd, step_name=""):
    """Print information about a point cloud"""
    print(f"\n--- {step_name} Information ---")
    print(f"Number of points (vertices): {len(pcd.points)}")
    print(f"Has colors: {pcd.has_colors()}")
    print(f"Has normals: {pcd.has_normals()}")

def print_voxel_info(voxel_grid, step_name=""):
    """Print information about a voxel grid"""
    print(f"\n--- {step_name} Information ---")
    voxels = voxel_grid.get_voxels()
    print(f"Number of voxels: {len(voxels)}")
    print(f"Has colors: {len(voxels) > 0}")
    print(f"Voxel size: {voxel_grid.voxel_size}")

# STEP 1: Loading and Visualization

print_separator(1, "Loading and Visualization")

# Load the 3D mesh file
mesh = o3d.io.read_triangle_mesh("Meetal nut.ply")

# Check if mesh has triangles, if not try loading as point cloud directly
if len(mesh.triangles) == 0:
    print("\nNote: Model has no triangles. Loading as point cloud instead...")
    pcd_direct = o3d.io.read_point_cloud("Meetal nut.ply")
    
    if len(pcd_direct.points) > 0:
        # Create a mesh from the point cloud for step 1
        print("Creating mesh from point cloud for visualization...")
        pcd_direct.estimate_normals()
        mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd_direct, depth=8)
        mesh.compute_vertex_normals()
    else:
        raise RuntimeError("Could not load model. Please check the file.")
else:
    # Compute normals if not present
    if not mesh.has_vertex_normals():
        mesh.compute_vertex_normals()

print("\nLoaded 3D model successfully!")
print_mesh_info(mesh, "Original Model")

print("\nDisplaying original mesh...")
print("(Close the window to continue to Step 2)")
o3d.visualization.draw_geometries([mesh], 
                                  window_name="Step 1: Original Mesh",
                                  width=800, height=600)

# STEP 2: Conversion to Point Cloud

print_separator(2, "Conversion to Point Cloud")

# Sample points from the mesh to create a point cloud
pcd = mesh.sample_points_uniformly(number_of_points=10000)

print("\nConverted mesh to point cloud!")
print_point_cloud_info(pcd, "Point Cloud")

print("\nDisplaying point cloud...")
print("(Close the window to continue to Step 3)")
o3d.visualization.draw_geometries([pcd], 
                                  window_name="Step 2: Point Cloud",
                                  width=800, height=600)

# STEP 3: Surface Reconstruction from Point Cloud
print_separator(3, "Surface Reconstruction from Point Cloud")

# Estimate normals for the point cloud
pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(
    radius=0.1, max_nn=30))

# Orient normals consistently
pcd.orient_normals_consistent_tangent_plane(k=15)

print("\nPerforming Poisson surface reconstruction...")
# Perform Poisson surface reconstruction
mesh_recon, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
    pcd, depth=9)

print("Surface reconstruction completed!")

# Remove low-density vertices (artifacts)
vertices_to_remove = densities < np.quantile(densities, 0.05)
mesh_recon.remove_vertices_by_mask(vertices_to_remove)

# Crop the mesh using bounding box to remove artifacts
bbox = pcd.get_axis_aligned_bounding_box()
mesh_cropped = mesh_recon.crop(bbox)

# Compute normals for the reconstructed mesh
mesh_cropped.compute_vertex_normals()

print("\nArtifacts removed using crop method!")
print_mesh_info(mesh_cropped, "Reconstructed Mesh")

print("\nDisplaying reconstructed mesh...")
print("(Close the window to continue to Step 4)")
o3d.visualization.draw_geometries([mesh_cropped], 
                                  window_name="Step 3: Reconstructed Mesh",
                                  width=800, height=600)

# STEP 4: Voxelization
print_separator(4, "Voxelization")

# Create voxel grid from point cloud
# Авто-выбор размера вокселя как 1-2% от максимальной размерности модели
bbox_extent = pcd.get_max_bound() - pcd.get_min_bound()
voxel_size = max(bbox_extent) * 0.02  # 2% от максимальной стороны
voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(pcd, voxel_size=voxel_size)
# Debug / диагностика voxel_grid


print("\nCreated voxel grid from point cloud!")
print_voxel_info(voxel_grid, "Voxel Grid")

print("\nDisplaying voxel grid...")
print("(Close the window to continue to Step 5)")
o3d.visualization.draw_geometries([voxel_grid], 
                                  window_name="Step 4: Voxel Grid",
                                  width=800, height=600)

# STEP 5: Adding a Plane

print_separator(5, "Adding a Plane")

# Get the center and extent of the point cloud
center = pcd.get_center()
extent = pcd.get_max_bound() - pcd.get_min_bound()

# Create a vertical plane that will cut through the bunny (same as Step 6 clipping plane)
plane_height = extent[1] * 1.5  # Height of plane
plane_depth = extent[2] * 1.5   # Depth of plane

# Create plane as a thin vertical box
plane = o3d.geometry.TriangleMesh.create_box(
    width=0.002,  # Very thin (vertical plane)
    height=plane_height, 
    depth=plane_depth)

# Position the plane at the center (where the cut will happen in Step 6)
plane_center = center.copy()
plane_center[0] = center[0]  # At the center X position (cutting plane)

# Translate plane to position
plane.translate(plane_center - plane.get_center())

# Color the plane red/orange to show it's a cutting plane
plane.paint_uniform_color([1.0, 0.3, 0.0])  # Orange-red cutting plane
plane.compute_vertex_normals()

# Create a copy of point cloud for visualization
pcd_with_plane = copy.deepcopy(pcd)

print("\nCreated a vertical cutting plane through the object!")
print(f"Plane dimensions: 0.002 x {plane_height:.3f} x {plane_depth:.3f}")
print(f"Plane position (center): {plane_center}")
print("This plane shows where the bunny will be cut in half in Step 6")

print("\nDisplaying object with cutting plane...")
print("(Close the window to continue to Step 6)")
o3d.visualization.draw_geometries([pcd_with_plane, plane], 
                                  window_name="Step 5: Object with Cutting Plane",
                                  width=800, height=600)

# STEP 6: Surface Clipping
print_separator(6, "Surface Clipping")

# Define a vertical clipping plane (remove points on the right side)
# Plane equation: ax + by + cz + d = 0
# We'll use a vertical plane through the center, removing the right half

# Get points as numpy array
points = np.asarray(pcd.points)

# Define plane normal (pointing left) and plane point (center)
plane_normal = np.array([1, 0, 0])  # Normal pointing right (we keep left side)
plane_point = center  # Plane passes through center

# Calculate which points are on the left side of the plane
# Point is on left if dot product of (point - plane_point) and normal is negative
distances = np.dot(points - plane_point, plane_normal)
mask = distances < 0  # Keep points with negative distance (left side)

# Create clipped point cloud
pcd_clipped = o3d.geometry.PointCloud()
pcd_clipped.points = o3d.utility.Vector3dVector(points[mask])

# Copy colors if they exist
if pcd.has_colors():
    colors = np.asarray(pcd.colors)
    pcd_clipped.colors = o3d.utility.Vector3dVector(colors[mask])

# Copy normals if they exist
if pcd.has_normals():
    normals = np.asarray(pcd.normals)
    pcd_clipped.normals = o3d.utility.Vector3dVector(normals[mask])

print("\nClipped point cloud (removed right half)!")
print_point_cloud_info(pcd_clipped, "Clipped Point Cloud")
print(f"Points removed: {len(pcd.points) - len(pcd_clipped.points)}")
print(f"Points remaining: {len(pcd_clipped.points)}")

# Note: For triangle mesh clipping, we would need to reconstruct
print("\nNote: Clipping performed on point cloud.")
print("For mesh clipping, reconstruction would be needed.")

print("\nDisplaying clipped point cloud...")
print("(Close the window to continue to Step 7)")
o3d.visualization.draw_geometries([pcd_clipped], 
                                  window_name="Step 6: Clipped Point Cloud",
                                  width=800, height=600)

# STEP 7: Working with Color and Extremes
print_separator(7, "Working with Color and Extremes")

# Work with the clipped point cloud
points = np.asarray(pcd_clipped.points)

# Choose axis for gradient (Z-axis - vertical)
axis = 2  # 0=X, 1=Y, 2=Z
axis_name = ['X', 'Y', 'Z'][axis]

# Get min and max along chosen axis
min_value = points[:, axis].min()
max_value = points[:, axis].max()

# Find extreme points
min_idx = np.argmin(points[:, axis])
max_idx = np.argmax(points[:, axis])
min_point = points[min_idx]
max_point = points[max_idx]

print(f"\nApplying color gradient along {axis_name}-axis...")
print(f"Minimum {axis_name} coordinate: {min_value:.4f} at point {min_point}")
print(f"Maximum {axis_name} coordinate: {max_value:.4f} at point {max_point}")

# Create color gradient (from blue to red)
normalized = (points[:, axis] - min_value) / (max_value - min_value)
colors = np.zeros((len(points), 3))
colors[:, 0] = normalized       # Red channel increases with height
colors[:, 2] = 1 - normalized   # Blue channel decreases with height

# Apply colors to point cloud
pcd_colored = copy.deepcopy(pcd_clipped)
pcd_colored.colors = o3d.utility.Vector3dVector(colors)
model_size = np.linalg.norm(pcd_clipped.get_max_bound() - pcd_clipped.get_min_bound())
sphere_radius = model_size * 0.02 
if len(points) == 0:
    raise RuntimeError("Clipped point cloud is empty! Check Step 6 clipping.")
# Create spheres to highlight extreme points
sphere_min = o3d.geometry.TriangleMesh.create_sphere(radius=sphere_radius)
sphere_min.translate(min_point)
sphere_min.paint_uniform_color([0, 1, 0])  # Green for minimum
sphere_min.compute_vertex_normals()

sphere_max = o3d.geometry.TriangleMesh.create_sphere(radius=sphere_radius)
sphere_max.translate(max_point)
sphere_max.paint_uniform_color([1, 1, 0])  # Yellow for maximum
sphere_max.compute_vertex_normals()

print(f"\nGradient applied! Colors range from blue (min) to red (max)")
print(f"Extreme points highlighted:")
print(f"  - Minimum (green sphere): {min_point}")
print(f"  - Maximum (yellow sphere): {max_point}")

print("\nDisplaying colored point cloud with extreme points...")
print("(Close the window to finish)")
o3d.visualization.draw_geometries([pcd_colored, sphere_min, sphere_max], 
                                  window_name="Step 7: Color Gradient & Extremes",
                                  width=800, height=600)

print("\n" + "="*80)
print("ALL 7 STEPS COMPLETED SUCCESSFULLY!")
print("="*80)
print("\nSummary:")
print("✓ Step 1: Loaded and visualized 3D mesh")
print("✓ Step 2: Converted to point cloud")
print("✓ Step 3: Reconstructed surface using Poisson")
print("✓ Step 4: Created voxel grid")
print("✓ Step 5: Added a plane to the scene")
print("✓ Step 6: Clipped surface (removed right half)")
print("✓ Step 7: Applied color gradient and highlighted extremes")
print("\nAssignment #5 Complete! Ready for defense.")
print("="*80 + "\n") 