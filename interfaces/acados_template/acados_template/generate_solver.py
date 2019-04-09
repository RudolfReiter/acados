from jinja2 import Environment, FileSystemLoader
from .generate_c_code_explicit_ode import *
from .generate_c_code_implicit_ode import *
from .generate_c_code_constraint import *
from .ocp_nlp_render_arguments import *
from ctypes import *

def generate_solver(model, acados_ocp, con_h=None, con_hN=None, con_p=None, con_pN=None, json_file='acados_ocp_nlp.json'):
    USE_TERA = 1 # EXPERIMENTAL: use Tera standalone parser instead of Jinja2

    ocp_nlp = acados_ocp
    ocp_nlp.cost = acados_ocp.cost.__dict__
    ocp_nlp.constraints = acados_ocp.constraints.__dict__
    ocp_nlp.solver_config = acados_ocp.solver_config.__dict__
    ocp_nlp.dims = acados_ocp.dims.__dict__
    ocp_nlp = ocp_nlp.__dict__

    ocp_nlp = dict2json(ocp_nlp)

    with open(json_file, 'w') as f:
        json.dump(ocp_nlp, f, default=np_array_to_list)

    with open(json_file, 'r') as f:
        ocp_nlp_json = json.load(f)

    ocp_nlp_dict = json2dict(ocp_nlp_json, ocp_nlp_json['dims'])

    acados_ocp = ocp_nlp_as_object(ocp_nlp_dict)
    acados_ocp.cost = ocp_nlp_as_object(acados_ocp.cost)
    acados_ocp.constraints = ocp_nlp_as_object(acados_ocp.constraints)
    acados_ocp.solver_config = ocp_nlp_as_object(acados_ocp.solver_config)
    acados_ocp.dims = ocp_nlp_as_object(acados_ocp.dims)

    # setting up loader and environment
    acados_path = os.path.dirname(os.path.abspath(__file__))
    if USE_TERA == 0:
        file_loader = FileSystemLoader(acados_path + '/c_templates')
        env = Environment(loader = file_loader)
    else:
        template_glob = acados_path + '/c_templates_tera/*'
        acados_template_path = acados_path + '/c_templates_tera'

    if acados_ocp.solver_config.integrator_type == 'ERK':
        # explicit model -- generate C code
        generate_c_code_explicit_ode(model)
    else:
        # implicit model -- generate C code
        opts = dict(generate_hess=1)
        generate_c_code_implicit_ode(model, opts)
    
    if con_p is not None and con_h is None:
        raise Exception('h constraint is missing!')

    if con_h is not None:
        # nonlinear part of nonlinear constraints 
        generate_c_code_constraint(con_h, '_h_constraint')

    if con_p is not None:
        # convex part of nonlinear constraints 
        generate_c_code_constraint(con_p, '_p_constraint')

    # check render arguments
    check_ra(acados_ocp)

    # create c_generated_code folder
    if not os.path.exists('c_generated_code'):
        os.mkdir('c_generated_code')

    if USE_TERA == 0:
        # render source template
        template = env.get_template('main.in.c')
        output = template.render(ocp=acados_ocp)
        # output file
        out_file = open('./c_generated_code/main_' + model.name + '.c', 'w+')
        out_file.write(output)
    else:
        os.chdir('c_generated_code')
        # render source template
        template_file = 'main.in.c'
        out_file = 'main_' + model.name + '.c'
        # output file
        os_cmd = 't_renderer ' + "\"" + template_glob + "\"" + ' ' + "\"" \
                + template_file + "\"" + ' ' + "\"" + '../' + json_file + \
                "\"" + ' ' + "\"" + out_file + "\""

        os.system(os_cmd)
        os.chdir('..')
        
    if USE_TERA == 0:
        # render source template
        template = env.get_template('acados_solver.in.c')
        output = template.render(ocp=acados_ocp)
        # output file
        out_file = open('./c_generated_code/acados_solver_' + model.name + '.c', 'w+')
        out_file.write(output)
    else:
        os.chdir('c_generated_code')
        # render source template
        template_file = 'acados_solver.in.c'
        out_file = 'acados_solver_' + model.name + '.c'
        # output file
        os_cmd = 't_renderer ' + "\"" + template_glob + "\"" + ' ' + "\"" \
                + template_file + "\"" + ' ' + "\"" + '../' + json_file + \
                "\"" + ' ' + "\"" + out_file + "\""

        os.system(os_cmd)
        os.chdir('..')

    if USE_TERA == 0:
        # render source template
        template = env.get_template('acados_solver.in.h')
        output = template.render(ocp=acados_ocp)
        # output file
        out_file = open('./c_generated_code/acados_solver_' + model.name + '.h', 'w+')
        out_file.write(output)
    else:
        os.chdir('c_generated_code')
        # render source template
        template_file = 'acados_solver.in.h'
        out_file = 'acados_solver_' + model.name + '.h'
        # output file
        os_cmd = 't_renderer ' + "\"" + template_glob + "\"" + ' ' + "\"" \
                + template_file + "\"" + ' ' + "\"" + '../' + json_file + \
                "\"" + ' ' + "\"" + out_file + "\""

        os.system(os_cmd)
        os.chdir('..')

    if USE_TERA == 0:
        # render header templates
        template = env.get_template('model.in.h')
        output = template.render(ocp=acados_ocp)
        # output file
        out_file = open('./c_generated_code/' + model.name + '_model/' + model.name + '_model.h', 'w+')
        out_file.write(output)
    else:
        os.chdir('c_generated_code/' + model.name + '_model/')
        # render source template
        template_file = 'model.in.h'
        out_file = model.name + '_model.h'
        # output file
        os_cmd = 't_renderer ' + "\"" + template_glob + "\"" + ' ' + "\"" \
                + template_file + "\"" + ' ' + "\"" + '../../' + json_file + \
                "\"" + ' ' + "\"" + out_file + "\""

        os.system(os_cmd)
        os.chdir('../..')

    if acados_ocp.dims.npd > 0:
        if USE_TERA == 0:
            # render header templates
            template = env.get_template('p_constraint.in.h')
            output = template.render(ocp=acados_ocp)
            # output file
            out_file = open('./c_generated_code/' + acados_ocp.con_p_name + '_p_constraint/' + acados_ocp.con_p_name + '_p_constraint.h', 'w+')
            out_file.write(output)
        else:
            os.chdir('c_generated_code/' + acados_ocp.con_p_name + '_p_constraint/')
            # render source template
            template_file = 'p_constraint.in.h'
            out_file = acados_ocp.con_p_name + '_p_constraint.h'
            # output file
            os_cmd = 't_renderer ' + "\"" + template_glob + "\"" + ' ' + "\"" \
                    + template_file + "\"" + ' ' + "\"" + '../../' + json_file + \
                    "\"" + ' ' + "\"" + out_file + "\""

            os.system(os_cmd)
            os.chdir('../..')

    if acados_ocp.dims.nh > 0:
        if USE_TERA == 0:
            # render header templates
            template = env.get_template('h_constraint.in.h')
            output = template.render(ocp=acados_ocp)
            # output file
            out_file = open('./c_generated_code/' + acados_ocp.con_h_name + '_h_constraint/' + acados_ocp.con_h_name + '_h_constraint.h', 'w+')
            out_file.write(output)
        else:
            os.chdir('c_generated_code/' + acados_ocp.con_h_name + '_h_constraint/')
            # render source template
            template_file = 'h_constraint.in.h'
            out_file = acados_ocp.con_h_name + '_h_constraint.h'
            # output file
            os_cmd = 't_renderer ' + "\"" + template_glob + "\"" + ' ' + "\"" \
                    + template_file + "\"" + ' ' + "\"" + '../../' + json_file + \
                    "\"" + ' ' + "\"" + out_file + "\""

            os.system(os_cmd)
            os.chdir('../..')

    if USE_TERA == 0:
        # render Makefile template
        template = env.get_template('Makefile.in')
        output = template.render(ocp=acados_ocp)

        # output file
        out_file = open('./c_generated_code/Makefile', 'w+')
        out_file.write(output)
    else:
        os.chdir('c_generated_code/') 
        # render source template
        template_file = 'Makefile.in'
        out_file = 'Makefile'
        # output file
        os_cmd = 't_renderer ' + "\"" + template_glob + "\"" + ' ' + "\"" \
                + template_file + "\"" + ' ' + "\"" + '../' + json_file + \
                "\"" + ' ' + "\"" + out_file + "\""

        os.system(os_cmd)
        os.chdir('..')

    if USE_TERA == 0:
        # render S-Function template
        template = env.get_template('acados_solver_sfun.in.c')
        output = template.render(ocp=acados_ocp)

        # output file
        out_file = open('./c_generated_code/acados_solver_sfunction_'  + model.name + '.c', 'w+')
        out_file.write(output)
    else:
        os.chdir('c_generated_code/') 
        # render source template
        template_file = 'acados_solver_sfun.in.c'
        out_file = 'acados_solver_sfunction_'  + model.name + '.c'
        # output file
        os_cmd = 't_renderer ' + "\"" + template_glob + "\"" + ' ' + "\"" \
                + template_file + "\"" + ' ' + "\"" + '../' + json_file + \
                "\"" + ' ' + "\"" + out_file + "\""

        os.system(os_cmd)
        os.chdir('..')

    if USE_TERA == 0:
        # render MATLAB make script
        template = env.get_template('make_sfun.in.m')
        output = template.render(ocp=acados_ocp)

        # output file
        out_file = open('./c_generated_code/make_sfun.m', 'w+')
        out_file.write(output)
    else:
        os.chdir('c_generated_code/') 
        # render source template
        template_file = 'make_sfun.in.m'
        out_file = 'acados_solver_sfun.in.c'
        # output file
        os_cmd = 't_renderer ' + "\"" + template_glob + "\"" + ' ' + "\"" \
                + template_file + "\"" + ' ' + "\"" + '../' + json_file + \
                "\"" + ' ' + "\"" + out_file + "\""

        os.system(os_cmd)
        os.chdir('..')

    # make 
    os.chdir('c_generated_code')
    os.system('make')
    os.system('make shared_lib')
    os.chdir('..')

    solver = acados_solver(acados_ocp, 'c_generated_code/acados_solver_' + model.name + '.so')
    solver.create()
    return solver

class acados_solver:
    def __init__(self, acados_ocp, shared_lib,):
        self.shared_lib = CDLL(shared_lib)
        self.nlp_opts = self.shared_lib.acados_get_nlp_opts()
        self.nlp_dims = self.shared_lib.acados_get_nlp_dims()
        self.nlp_config = self.shared_lib.acados_get_nlp_config()
        self.nlp_out = self.shared_lib.acados_get_nlp_out()
        self.nlp_in = self.shared_lib.acados_get_nlp_in()
        self.acados_ocp = acados_ocp

    def create(self):
        self.shared_lib.acados_create()

    def solve(self):
        self.shared_lib.acados_solve()

    def free(self):
        self.shared_lib.acados_free()

    def get(self, stage, field_):

        field = field_
        field = field.encode('utf-8')
        import pdb; pdb.set_trace()

        self.shared_lib.ocp_nlp_dims_get.argtypes = [c_void_p, c_void_p, c_void_p, c_int, c_char_p]
        self.shared_lib.ocp_nlp_dims_get.restype = c_int
        import pdb; pdb.set_trace()
        x0 = np.ascontiguousarray(np.zeros((4,1)), dtype=np.float64)
        x0 = cast(x0.ctypes.data, POINTER(c_double))
        self.shared_lib.ocp_nlp_out_get(self.nlp_config, self.nlp_dims, self.nlp_out, 1, "x", x0);
        import pdb; pdb.set_trace()
        dims = self.shared_lib.ocp_nlp_dims_get(self.nlp_config, self.nlp_dims, self.nlp_out, stage, field)
        out = np.ascontiguousarray(np.zeros((4,1)), dtype=np.float64)
        out = cast(out.ctypes.data, POINTER(c_double))
        self.shared_lib.ocp_nlp_out_get(self.nlp_config, self.nlp_dims, self.nlp_out, stage, field, out);
        return out



