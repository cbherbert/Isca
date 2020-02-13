import numpy as np
import sys

from isca import DryCodeBase, DiagTable, Experiment, Namelist, GFDL_BASE

NCORES = 16
RESOLUTION = 'T42', 25  # T42 horizontal resolution, 25 levels in pressure

# a CodeBase can be a directory on the computer,
# useful for iterative development
#cb = DryCodeBase.from_directory(GFDL_BASE)

# or it can point to a specific git repo and commit id.
# This method should ensure future, independent, reproducibility of results.
# cb = DryCodeBase.from_repo(repo='https://github.com/isca/isca', commit='isca1.1')

#cb.compile()  # compile the source code to working directory $GFDL_WORK/codebase


class MatsunoGillExperiment(Experiment):
    """
    This class subclasses the Experiment class for easily setting up Matsuno Gill experiments,
    with a prescribed non-zonal tropical heating term of the form Q0*cos(kx)*exp(-y**2/2).

    Parameters
    ----------
    name : str
        The name of the experiment, used for the directory containing the model output.

    Keyword Arguments
    -----------------
    codebase : CodeBase object
        Version of the code to use. Can be a directory or a git repo and commit id.
        Default is GFDL_BASE environment variable.
    output_freq : int
        Output frequency, in days (default 90)
    namelist_mod : dict
        Dictionary used to update the default namelist parameters for the experiment.
        Be careful that it should actually be a dictionnary of dictionnaries, each
        corresponding to a namelist.
    """
    def __init__(self, name, codebase=DryCodeBase.from_directory(GFDL_BASE),
                 output_freq=90, namelist_mod={}, **kwargs):
        # Compile the source code to working directory $GFDL_WORK/codebase
        codebase.compile()
        # compilation depends on computer specific settings.  The $GFDL_ENV
        # environment variable is used to determine which `$GFDL_BASE/src/extra/env` file
        # is used to load the correct compilers.  The env file is always loaded from
        # $GFDL_BASE and not the checked out git repo.

        # Initialize the Experiment object to handle the configuration of model parameters
        # and output diagnostics

        Experiment.__init__(self, name, codebase)

        self.diag_table = self.build_diag_table(output_freq, False)

        namelist = self.default_namelist()
        for key in namelist_mod:
            if key in namelist:
                namelist[key].update(namelist_mod[key])
            else:
                namelist[key] = namelist_mod[key]
        self.namelist = Namelist(namelist)

        if 'resolution' in kwargs:
            self.set_resolution(*kwargs['resolution'])

    @classmethod
    def build_diag_table(cls, output_freq, output_avg):
        """
        Return the diagnostic table for the experiment.
        """
        #Tell model how to write diagnostics
        diag = DiagTable()
        diag.add_file('atmos_monthly', output_freq, 'days', time_units='days')

        #Tell model which diagnostics to write
        diag.add_field('dynamics', 'ps', time_avg=output_avg)
        diag.add_field('dynamics', 'bk')
        diag.add_field('dynamics', 'pk')
        diag.add_field('dynamics', 'ucomp', time_avg=output_avg)
        diag.add_field('dynamics', 'vcomp', time_avg=output_avg)
        diag.add_field('dynamics', 'temp', time_avg=output_avg)
        diag.add_field('dynamics', 'vor', time_avg=output_avg)
        diag.add_field('dynamics', 'div', time_avg=output_avg)
        diag.add_field('hs_forcing', 'q_eqf', time_avg=output_avg)

        return diag

    @classmethod
    def default_namelist(cls):
        """
        Return the default namelist for the experiment.
        """
        # define namelist values as python dictionary
        # wrapped as a namelist object.
        namelist = {
            'main_nml': {
                'dt_atmos': 300,
                'days': 1800,
                'current_time': 0,
                'calendar': 'no_calendar'
            },

            'atmosphere_nml': {
                'idealized_moist_model': False  # False for Newtonian Cooling.  True for Isca/Frierson
            },

            'spectral_dynamics_nml': {
                'damping_order'           : 4,                      # default: 2
                'water_correction_limit'  : 200.e2,                 # default: 0
                'reference_sea_level_press': 1.0e5,                  # default: 101325
                'valid_range_t'           : [100., 800.],           # default: (100, 500)
                'initial_sphum'           : 0.0,                  # default: 0
                'vert_coord_option'       : 'uneven_sigma',         # default: 'even_sigma'
                'scale_heights': 6.0,
                'exponent': 7.5,
                'surf_res': 0.5
            },

            # configure the relaxation profile
            'hs_forcing_nml': {
                't_zero': 315.,    # temperature at reference pressure at equator (default 315K)
                't_strat': 200.,   # stratosphere temperature (default 200K)
                'delh': 40.,       # equator-pole temp gradient (default 60K)
                'delv': 10.,       # lapse rate (default 10K)
                'eps': 0.,         # stratospheric latitudinal variation (default 0K)
                'sigma_b': 0.7,    # boundary layer friction height (default p/ps = sigma = 0.7)

                # negative sign is a flag indicating that the units are days
                'ka':   -40.,      # Constant Newtonian cooling timescale (default 40 days)
                'ks':    -4.,      # Boundary layer dependent cooling timescale (default 4 days)
                'kf':   -1.,       # BL momentum frictional timescale (default 1 days)

                'do_conserve_energy':   True,  # convert dissipated momentum into heat (default True)
            },

            'atf_forcing_nml': {
                'q0atf': 0.0 # Amplitude of the non-zonal heating term
            },

            'diag_manager_nml': {
                'mix_snapshot_average_fields': False
            },

            'fms_nml': {
                'domains_stack_size': 600000                        # default: 0
            },

            'fms_io_nml': {
                'threading_write': 'single',                         # default: multi
                'fileset_write': 'single',                           # default: multi
            }
            }
        return namelist


exp = MatsunoGillExperiment('superrotation_nzforcing_q1_long',
                            output_freq=1000,
                            namelist_mod={'atf_forcing_nml': {'q0atf': 1.0, 'cfatf': 0, 'katf': 2,
                                                              'dphiatf': 10.0},
                                          'main_nml': {'days': 18000}},
                            resolution=RESOLUTION)
#exp.set_resolution(*RESOLUTION)

#Lets do a run!
if __name__ == '__main__':
    exp.run(1, num_cores=NCORES, use_restart=False, mpirun_opts=' '.join(sys.argv[1:]))
    #for i in range(2, 21):
    #    exp.run(i, num_cores=NCORES)  # use the restart i-1 by default
