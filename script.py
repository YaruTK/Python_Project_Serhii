import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkCommonColor

from vtkmodules.vtkFiltersSources import (
    vtkCylinderSource,
    vtkCubeSource
)
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer
)

# dictionary for further improvement of the simulation
material_dict = {}

def add_material(name: str, material_properties: tuple):
    if name not in material_dict:
        material_dict[name] = material_properties
    else: 
        raise Exception("Such material already exists")
    
def get_material_list():
    return material_dict.keys()

# common class for all structures, inherited by more complex classes
class Structure:
    def __init__(self, name: str, mass: float, material: str, *dimensions: float):
        self._name = name
        self._mass = mass
        if material not in material_dict:
            raise Exception("No such material known")
        else:
            self._material = material
        self._dim = []
        if len(dimensions) != 2:
            raise ValueError("Need exactly 2 dimensions")
        else:
            self._dim = sorted(dimensions)

    def get_dimensions(self):
        return self._dim

    def get_material(self):
        return self._material

    def __str__(self):
        return "This is a %s %s of %d kg mass, made of %s. The size is %dx%d" % (self.__class__.__name__, self._name, self._mass, self._material, self._dim[0], self._dim[1])

# list of Structure objects for iteration reasons (further will be for choosing a part from the list)
structure_list = []

# Rotor class, includes efficiency, model and max_rpm arguments
class Rotor(Structure):
    def __init__(self,  name: str, mass: float, material: str, max_rpm: float, model: str,  efficiency: float, *dimensions: float):
        super().__init__(name, mass, material, *dimensions)
        self._max_rpm = max_rpm
        self._model = model
        self._efficiency = efficiency

rotor_list = []

# wing class, for assembly of a fan
class Wing(Structure):
        def __init__(self,  name: str, mass: float, material: str, number_of_wings: int, *dimensions: float):
            super().__init__(name, mass, material, *dimensions)
            self._now = number_of_wings

wing_list = []


# the core class which assembles a windmill from parts, creates all required vtkObjects and renders it
class Windmill():
    def __init__(self, fund: Structure, tube: Structure, rotor: Rotor, wing: Wing):
        self._fund = fund
        self._tube = tube
        self._wing = wing
        self._rotor = rotor
        self.vtk_parts_list = []
        self.vtk_actors_list = []
    
    
    def create_vtkCubeSource(self, struct, center, l, w, h):
        vtk_obj = vtkCubeSource()
        vtk_obj.SetCenter(center)
        vtk_obj.SetXLength(l)
        vtk_obj.SetYLength(h)
        vtk_obj.SetZLength(w)
        vtk_obj.structure = struct

        return vtk_obj
    
    
    def create_vtkCylinderSource(self, struct, center, d, h, resolution = 100):
        vtk_obj = vtkCylinderSource()
        vtk_obj.SetCenter(center)
        vtk_obj.SetRadius(d/2)
        vtk_obj.SetHeight(h)
        vtk_obj.SetResolution(resolution)
        vtk_obj.structure = struct

        return vtk_obj

    
    def assemble(self):
        self.vtk_parts_list = []  # new assembly -- new parts

        # calculate all dimensions for all parts
        tube_d, tube_h = self._tube.get_dimensions()  
        fund_w, fund_l = self._fund.get_dimensions()  
        fund_h = tube_h * 0.1 
        rotor_h, rotor_w = self._rotor.get_dimensions()
        rotor_l = rotor_w
        wing_w, wing_l = self._wing.get_dimensions()
        wing_h = wing_w * 0.1
        
        # calculate all center positions
        self._fund_center = (0.0, -0.5 * fund_h, 0.0)
        self._tube_center = (0.0, tube_h * 0.5, 0.0)
        self._rotor_center = (0.0, tube_h + rotor_h * 0.5, 0.0)
        self._fan_center = (0.0, tube_h + rotor_h * 0.5, rotor_w * 0.5 + wing_h * 0.5)

        # create vtkSources for each part, Fundament, rotor and TEMPORARELY wing are cubes, tube is cylinder
        self.Fundament_vtkSource = self.create_vtkCubeSource(self._fund, self._fund_center, fund_l, fund_w, fund_h)
        self.vtk_parts_list.append(self.Fundament_vtkSource)

        self.Rotor_vtkSource = self.create_vtkCubeSource(self._rotor, self._rotor_center, rotor_l, rotor_w, rotor_h)
        self.vtk_parts_list.append(self.Rotor_vtkSource)

#NEED TO CHANGE
        self.Fan_vtkSource = self.create_vtkCubeSource(self._wing, self._fan_center, wing_l, wing_h, wing_w) 
        self.vtk_parts_list.append(self.Fan_vtkSource)
#NEED TO CHANGE
        
        self.Tube_vtkSource = self.create_vtkCylinderSource(self._tube, self._tube_center, tube_d, tube_h, 10)
        self.vtk_parts_list.append(self.Tube_vtkSource)

        return self.vtk_parts_list
    

    def create_vtkActor(self, vtk_obj):

        # each actor requires mapper
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(vtk_obj.GetOutputPort())
        
        actor = vtkActor()
        actor.SetMapper(mapper)

        # getting color of material through the dictionary
        material = vtk_obj.structure.get_material()
        color = tuple(i/255 for i in material_dict[material][0])  # change 0-255 to 0.0-1.0

        #for fun
        actor.GetProperty().EdgeVisibilityOn()
        actor.GetProperty().SetLineWidth(2)
        
        actor.GetProperty().SetColor(color)
        #actor.GetProperty().Modified()
        
        return actor
    

    def initiate_all_actors(self):
        # module that iterates through assembled parts and creates an actor for each part
        self.vtk_actors_list = []
        for vtk_part in self.vtk_parts_list:
            actor = self.create_vtkActor(vtk_part)
            self.vtk_actors_list.append(actor)

        return self.vtk_actors_list


    def render(self, lst):
        # Create a renderer, render window, and window interactor (requires refinement)
        renderer = vtkRenderer()
        renderWindow = vtkRenderWindow()
        renderWindow.AddRenderer(renderer)
        renderWindowInteractor = vtkRenderWindowInteractor()
        renderWindowInteractor.SetRenderWindow(renderWindow)
                
        for actor in lst:
            renderer.AddActor(actor)
                
        renderer.SetBackground(.8,.8,.8)
        renderWindow.Render()
        renderWindowInteractor.Start()


    def change_rotation_speed(self):
        pass


    def change_part(self):
        pass


add_material("Steel", ((227, 213, 215), 600, 90))  # colour, how strong it is, how it heats (for future)
add_material("Wood", ((102, 46, 16), 100, 30))
add_material("Glass", ((209, 243, 255), 20, 40))
add_material("Concrete", ((124, 135, 135), 200, 20))

#                         name    |  mass  | materal  | dimensions
Fundament1 = Structure("Fundament", 1000.0, "Concrete", 40, 40)
structure_list.append(Fundament1)

#               name  |mass|material|max_rpm|model|effic|dimensions
Rotor1 = Rotor("Rotor", 420, "Steel", 1400, "mk. 1", 0.6, 8, 6)   
rotor_list.append(Rotor1)

#               name    | mass |materal| dimensions
Tube1 = Structure("Tube", 650.0, "Glass", 4, 60)
structure_list.append(Tube1)

#               name| mass | mat.| num. of wings| dimensions
Wing1 = Wing("Wing 3x", 80, "Wood", 3, 30, 4)
wing_list.append(Wing1)

# assemble the windmill
Windmill1 = Windmill(Fundament1, Tube1, Rotor1, Wing1)

if __name__ == '__main__':
    Windmill1.assemble()
    list_of_actors = Windmill1.initiate_all_actors()
    Windmill1.render(list_of_actors)
