# Python 2 compatibility
from __future__ import division
from __future__ import print_function

# Standard libraries
from itertools import product
from argparse import ArgumentParser
# More Python 2 compatibility
if sys.version_info.major == 2:
    from itertools import izip as zip

# Related modules
try:
    import numpy as np
except ImportError:
    print('Error: NumPy must be installed.')
    raise
try:
    import cantera as ct
    from cantera import ck2cti
except ImportError:
    print('Error: Cantera must be installed.')
    raise
try:
    import yaml
except ImportError:
    print('Warning: YAML must be installed to read input file.')


class Stream(object):
    def __init__(self, gas, flow):
        self.comp = np.hstack((gas.enthalpy_mass, gas.Y))
        self.flow = flow

        # Running variable of flow rate
        self.xflow = 0.0

    def __call__(self):
        return self.comp


class Particle(object):
    def __init__(self, gas):
        self.gas = gas
        self.reac = ct.IdealGasConstPressureReactor(self.gas)
        self.netw = ct.ReactorNet([self.reac])

    def __call__(self, comp=None):
        """Return or set composition.
        """
        if comp is not None:
            if isinstance(comp, Particle):
                h = comp.gas.enthalpy_mass
                Y = comp.gas.Y
            elif isinstance(comp, np.ndarray):
                h = comp[0]
                Y = comp[1:]
            else:
                return NotImplemented
            self.gas.HPY = h, self.gas.P, Y
            self.reac.syncState()
            self.netw.reinitialize()
        else:
            return np.hstack((self.gas.enthalpy_mass, self.gas.Y))

    def __add__(self, other):
        if isinstance(other, Particle):
            h = self.gas.enthalpy_mass + other.gas.enthalpy_mass
            Y = self.gas.Y + other.gas.Y
            return np.hstack((h, Y))
        elif isinstance(other, np.ndarray):
            h = self.gas.enthalpy_mass + other[0]
            Y = self.gas.Y + other[1:]
            return np.hstack((h, Y))
        elif isinstance(other, (int, float)):
            h = self.gas.enthalpy_mass + other
            Y = self.gas.Y + other
            return np.hstack((h, Y))
        else:
            return NotImplemented

    def __radd__(self, other):
        if isinstance(other, Particle):
            h = self.gas.enthalpy_mass + other.gas.enthalpy_mass
            Y = self.gas.Y + other.gas.Y
            return np.hstack((h, Y))
        elif isinstance(other, np.ndarray):
            h = self.gas.enthalpy_mass + other[0]
            Y = self.gas.Y + other[1:]
            return np.hstack((h, Y))
        elif isinstance(other, (int, float)):
            h = self.gas.enthalpy_mass + other
            Y = self.gas.Y + other
            return np.hstack((h, Y))
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Particle):
            h = self.gas.enthalpy_mass - other.gas.enthalpy_mass
            Y = self.gas.Y - other.gas.Y
            return np.hstack((h, Y))
        elif isinstance(other, np.ndarray):
            h = self.gas.enthalpy_mass - other[0]
            Y = self.gas.Y - other[1:]
            return np.hstack((h, Y))
        elif isinstance(other, (int, float)):
            h = self.gas.enthalpy_mass - other
            Y = self.gas.Y - other
            return np.hstack((h, Y))
        else:
            return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, Particle):
            h = other.gas.enthalpy_mass - self.gas.enthalpy_mass
            Y = other.gas.Y - self.gas.Y
            return np.hstack((h, Y))
        elif isinstance(other, np.ndarray):
            h = other[0] - self.gas.enthalpy_mass
            Y = other[1:] - self.gas.Y
            return np.hstack((h, Y))
        elif isinstance(other, (int, float)):
            h = other - self.gas.enthalpy_mass
            Y = other - self.gas.Y
            return np.hstack((h, Y))
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return (np.hstack((self.gas.enthalpy_mass, self.gas.Y)) * other)
        else:
            return NotImplemented

    def __rmul__(self, other):
        if isinstance(other, (int, float)):
            return (np.hstack((self.gas.enthalpy_mass, self.gas.Y)) * other)
        else:
            return NotImplemented

    def __iadd__(self, other):
        if isinstance(other, Particle):
            h = self.gas.enthalpy_mass + other.gas.enthalpy_mass
            Y = self.gas.Y + other.gas.Y
        elif isinstance(other, np.ndarray):
            h = self.gas.enthalpy_mass + other[0]
            Y = self.gas.Y + other[1:]
        elif isinstance(other, (int, float)):
            h = self.gas.enthalpy_mass + other
            Y = self.gas.Y + other
        else:
            return NotImplemented
        self.gas.HPY = h, self.gas.P, Y
        self.reac.syncState()
        self.netw.reinitialize()
        return self

    def __isub__(self, other):
        if isinstance(other, Particle):
            h = self.gas.enthalpy_mass - other.gas.enthalpy_mass
            Y = self.gas.Y - other.gas.Y
        elif isinstance(other, np.ndarray):
            h = self.gas.enthalpy_mass - other[0]
            Y = self.gas.Y - other[1:]
        elif isinstance(other, (int, float)):
            h = self.gas.enthalpy_mass - other
            Y = self.gas.Y - other
        else:
            return NotImplemented
        self.gas.HPY = h, self.gas.P, Y
        self.reac.syncState()
        self.netw.reinitialize()
        return self

    def __imul__(self, other):
        if isinstance(other, (int, float)):
            h = self.gas.enthalpy_mass * other
            Y = self.gas.Y * other
        else:
            return NotImplemented
        self.gas.HPY = h, self.gas.P, Y
        self.reac.syncState()
        self.netw.reinitialize()
        return self


def equivalence_ratio(gas, eq_ratio, fuel, oxidizer, complete_products):
    """Calculate the mixture mole fractions from the equivalence ratio.

    Given the equivalence ratio, fuel mixture, oxidizer mixture,
    the products of complete combustion, and any additional species for
    the mixture, return a string containing the mole fractions of the
    species, suitable for setting the state of the input ThermoPhase.

    :param gas:
        Cantera ThermoPhase object containing the desired species.
    :param eq_ratio:
        Equivalence ratio
    :param fuel:
        Dictionary of molecules in the fuel mixture and the fraction of
        each molecule in the fuel mixture
    :param oxidizer:
        Dictionary of molecules in the oxidizer mixture and the
        fraction of each molecule in the oxidizer mixture.
    :param complete_products:
        List of species in the products of complete combustion.
    """
    reactants = ''
    cprod_elems = {}
    fuel_elems = {}
    oxid_elems = {}

    # Check sum of fuel and oxidizer values; normalize if greater than 1
    fuel_sum = sum(fuel.values())
    if fuel_sum > 1.0:
        for sp, x in fuel.items():
            fuel[sp] = x / fuel_sum

    oxid_sum = sum(oxidizer.values())
    if oxid_sum > 1.0:
        for sp, x in oxidizer.items():
            oxidizer[sp] = x / oxid_sum

    # Check oxidation state of complete products
    for sp, el in product(complete_products, gas.element_names):
        if el.upper() not in cprod_elems:
            cprod_elems[el.upper()] = {}

        cprod_elems[el.upper()][sp] = int(gas.n_atoms(sp, el))

    num_C_cprod = sum(cprod_elems.get('C', {0: 0}).values())
    num_H_cprod = sum(cprod_elems.get('H', {0: 0}).values())
    num_O_cprod = sum(cprod_elems.get('O', {0: 0}).values())

    oxid_state = 4*num_C_cprod + num_H_cprod - 2*num_O_cprod
    if oxid_state != 0:
        print('Warning: One or more products of incomplete combustion '
              'were specified.')

    # Find the number of H, C, and O atoms in the fuel molecules.
    for sp, el in product(fuel.keys(), gas.element_names):
        if el not in fuel_elems:
            fuel_elems[el.upper()] = 0

        fuel_elems[el.upper()] += gas.n_atoms(sp, el) * fuel[sp]

    num_C_fuel = fuel_elems.get('C', 0)
    num_H_fuel = fuel_elems.get('H', 0)
    num_O_fuel = fuel_elems.get('O', 0)

    # Find the number of H, C, and O atoms in the oxidizer molecules.
    for sp, el in product(oxidizer.keys(), gas.element_names):
        if el not in oxid_elems:
            oxid_elems[el.upper()] = 0

        oxid_elems[el.upper()] += gas.n_atoms(sp, el) * oxidizer[sp]

    num_O_oxid = oxid_elems.get('O', 0)

    # Check that all of the elements specified in the fuel and oxidizer
    # are present in the complete products and vice versa.
    for el in cprod_elems.keys():
        if ((sum(cprod_elems[el].values()) > 0 and fuel_elems[el] == 0 and
             oxid_elems[el] == 0) or (sum(cprod_elems[el].values()) == 0 and
            (fuel_elems[el] > 0 or oxid_elems[el] > 0))):
            print('Error: Must specify all elements in the fuel + oxidizer '
                  'in the complete products and vice-versa')
            sys.exit(1)

    # Compute the amount of oxidizer required to consume all the
    # carbon and hydrogen in the complete products
    if num_C_cprod > 0:
        spec = cprod_elems['C'].keys()
        ox = sum([cprod_elems['O'][sp]
                  for sp in spec if cprod_elems['C'][sp] > 0])
        C_multiplier = ox/num_C_cprod
    else:
        C_multiplier = 0

    if num_H_cprod > 0:
        spec = cprod_elems['H'].keys()
        ox = sum([cprod_elems['O'][sp]
                  for sp in spec if cprod_elems['H'][sp] > 0])
        H_multiplier = ox/num_H_cprod
    else:
        H_multiplier = 0

    # Compute how many O atoms are required to oxidize everybody
    num_O_req = (num_C_fuel * C_multiplier +
                 num_H_fuel * H_multiplier - num_O_fuel)
    O_mult = num_O_req/num_O_oxid

    # Find the total number of moles in the fuel + oxidizer mixture
    total_oxid_moles = sum([O_mult * amt for amt in oxidizer.values()])
    total_fuel_moles = sum([eq_ratio * amt for amt in fuel.values()])
    total_reactant_moles = total_oxid_moles + total_fuel_moles

    # Compute the mole fractions of the fuel and oxidizer components
    # given that a certain portion of the mixture will have been taken
    # up by the additional species, if any.
    for species, ox_amt in oxidizer.items():
        molefrac = ox_amt * O_mult/total_reactant_moles
        add_spec = ':'.join([species, str(molefrac)])
        reactants = ','.join([reactants, add_spec])

    for species, fuel_amt in fuel.items():
        molefrac = fuel_amt*eq_ratio/total_reactant_moles
        add_spec = ':'.join([species, str(molefrac)])
        reactants = ','.join([reactants, add_spec])

    # Take off the first character, which is a comma
    reactants = reactants[1:]
    return reactants


def pairwise(iterable):
    """s -> (s0,s1), (s2,s3), (s4, s5), ...
    """
    a = iter(iterable)
    return zip(a, a)


def mix_substep(particles, dt, tau_mix):
    """Pairwise mixing step.

    :param particles:
        List of Particle objects.
    :param dt:
        Time step [s] to increment particles.
    :param tau_mix:
        Mixing timescale [s].
    """

    decay = 0.5 * (1.0 - np.exp(-2.0 * dt / tau_mix))
    for p1, p2 in pairwise(particles):
        delt = (p1 - p2) * decay
        p1 -= delt
        p2 += delt

        # Update with new compositions
        comp1 = p1()
        comp2 = p2()
        particles[particles.index(p1)](comp1)
        particles[particles.index(p2)](comp2)


def reaction_substep(particles, end_time):
    """Advance each of the particles in time through reactions.

    :param particles:
        List of Particle objects.
    :param dt:
        Time step [s] to increment particles.
    """
    for p in particles:
        p.netw.advance(end_time)


def select_pairs(particles, num_pairs, num_skip=0):
    """Randomly select pair(s) of particles and move to end of list.

    :param particles:
        List of Particle objects.
    :param num_pairs:
        Number of pairs to be selected and moved.
    :param num_skip:
        Number of pairs at end of list to be skipped. Optional, default 0.
    """

    for i_pair in range(num_pairs):
        i = 2 * np.random.randint((len(particles) // 2) - i_pair - num_skip)
        j = i + 1

        # Commute particles at random
        if np.random.random() > 0.5:
            temp_comp = particles[i]()
            particles[i](particles[j]())
            particles[j](temp_comp)
            #particles[i], particles[j] = particles[j], particles[i]

        # Move to end of list
        particles.append(particles.pop(i))
        particles.append(particles.pop(i))
        # Swap with pair at end of list
        #i_last = -2 * (i_pair + 1)
        #particles[i], particles[i_last] = particles[i_last], particles[i]
        #particles[i+1], particles[i_last+1] = particles[i_last+1], particles[i+1]


def inflow(streams):
    """Determine index of stream for next inflowing particle.

    :param streams:
        List of Stream objects for inlet streams.
    """

    # Find stream with largest running flow rate
    sum_flows = 0.0
    fl_max = 0.0
    i_inflow = None
    for i, stream in enumerate(streams):
        streams[i].xflow += stream.flow
        sum_flows += stream.flow

        if streams[i].xflow > fl_max:
            fl_max = streams[i].xflow
            i_inflow = i

    # Check sum of flows
    if sum_flows < 0.0:
        print('Error: sum_flows = {:.4}'.format(sum_flows))
        sys.exit(1)

    # Now reduce running flow rate of selected stream
    streams[i_inflow].xflow -= sum_flows
    return i_inflow


def save_data(idx, time, particles, data):
    """Save temperature and species mass fraction from all particles to array.

    :param idx:
        Index of timestep.
    :param time:
        Current time [s].
    :param particles:
        List of Particle objects.
    :param data:
        ndarray of particle data for all timesteps.
    """
    for i, p in enumerate(particles):
        data[idx, i, 0] = time
        data[idx, i, 1] = p.gas.T
        data[idx, i, 2:] = p()[1:]


def partially_stirred_reactor(mech, case, init_temp, pres, eq_ratio, fuel,
                              oxidizer, complete_products=['CO2','H2O','N2'],
                              num_part=100, tau_res=(10./1000.),
                              tau_mix=(1./1000.), tau_pair=(1./1000.),
                              num_res=5
                              ):
    """Perform partially stirred reactor (PaSR) simulation.

    :param mech:
        Mechanism filename (in Cantera format).
    :param case:
        'Premixed' or 'Non-premixed'.
    :param init_temp:
        Initial temperature [K].
    :param pres:
        Pressure [atm].
    :param eq_ratio:
        Equivalence ratio.
    :param fuel:
        Dictionary of molecules in the fuel mixture and the fraction of
        each molecule in the fuel mixture.
    :param oxidizer:
        Dictionary of molecules in the oxidizer mixture and the
        fraction of each molecule in the oxidizer mixture.
    :param complete_products:
        List of species in the products of complete combustion.
        Optional, default [CO2, H2O, N2].
    :param num_part:
        Number of particles. Optional, default 100.
    :param tau_res:
        Residence time [s]. Optional, default 10 [ms].
    :param tau_mix:
        Mixing timescale [s]. Optional, default 1 [ms].
    :param tau_pair:
        Pairing timescale [s]. Optional, default 1 [ms].
    :param num_res:
        Numer of residence times to simulate. Optional, default 5.
    """

    # Time step control
    # Potential for adjusting time step, but unused for now.
    dt_max = 0.1 * min(tau_res, tau_pair)
    dt_min = dt_max
    dt_avg = 0.5 * (dt_max + dt_min)

    dt_sub = 0.040 * tau_mix
    num_substeps = 1 + int(dt_max / dt_sub)

    time_end = num_res * tau_res
    num_steps = int(time_end / dt_avg)

    # Set initial conditions
    gas = ct.Solution(mech)

    # Determine reactants
    reactants = equivalence_ratio(gas, eq_ratio, fuel,
                                  oxidizer, complete_products
                                  )

    # Inlet streams
    if case.lower() == 'premixed':
        # Premixed
        flow_rates = dict(fuel_air = 0.95, pilot = 0.05)
    elif case.lower() == 'non-premixed':
        # Non-premixed
        flow_rates = dict(air = 0.85, fuel = 0.05, pilot = 0.1)
    else:
        print('Error: case needs to be either premixed or non-premixed.')
        sys.exit(1)

    inlet_streams = []
    for src in flow_rates.keys():
        if src == 'fuel':
            reacs = ''
            for sp, amt in fuel.items():
                add_sp = ':'.join([sp, str(amt)])
                reacs = ','.join([reacs, add_sp])
            reacs = reacs[1:]

            gas.TPX = init_temp, pres * ct.one_atm, fuel + ':1.0'
            fuel_stream = Stream(gas, flow_rates['fuel'])
            inlet_streams.append(fuel_stream)
        elif src == 'air':
            reacs = ''
            for sp, amt in oxidizer.items():
                add_sp = ':'.join([sp, str(amt)])
                reacs = ','.join([reacs, add_sp])
            reacs = reacs[1:]

            gas.TPX = init_temp, pres * ct.one_atm, 'O2:0.21,N2:0.79'
            air_stream = Stream(gas, flow_rates['air'])
            inlet_streams.append(air_stream)
        elif src == 'fuel_air':
            gas.TPX = init_temp, pres * ct.one_atm, reactants
            fuel_air_stream = Stream(gas, flow_rates['fuel_air'])
            inlet_streams.append(fuel_air_stream)

    # Pilot always present
    # Get equilibrium composition for pilot and initial conditions
    gas.TPX = init_temp, pres * ct.one_atm, reactants
    gas.equilibrate('HP')
    pilot_stream = Stream(gas, flow_rates['pilot'])
    inlet_streams.append(pilot_stream)

    # Initialize all particles with pilot composition
    particles = []
    for i in range(num_part):
        g = ct.Solution(mech)
        g.TPX = gas.T, gas.P, gas.X
        particles.append(Particle(g))

    # Random seed
    np.random.seed()

    time = 0.0
    i_step = 0

    part_out = 0.0
    part_pair = 0.0

    times = np.zeros(num_steps + 2)
    temp_mean = np.zeros(num_steps + 2)
    temp_mean[0] = np.mean([p.gas.T for p in particles])

    # Array of full particle data for all timesteps
    particle_data = np.empty([num_steps + 2, num_part, gas.n_species + 2])
    save_data(i_step, time, particles, particle_data)

    print('Time [ms]  Temperature [K]')
    temp_mean[i_step] = np.mean([p.gas.T for p in particles])
    print('{:6.2f}  {:9.1f}'.format(time*1000., temp_mean[i_step]))

    while time < time_end:
        if (time + dt_max) > time_end:
            dt = time_end - time
        else:
            dt = dt_max

        part_out += num_part * dt / tau_res
        npart_out = int(round(part_out))
        part_out -= npart_out

        # Select num_pairs random pairs of particles for each
        # inflow/outflow particle and shift to end.
        num_fl_pairs = 2 * npart_out
        select_pairs(particles, num_fl_pairs)

        # Set alternate particles to inflow properties
        for i in range(npart_out):
            i_str = inflow(inlet_streams)
            particles[1 - 2 * (i+1)](inlet_streams[i_str]())

        # Now perform pairing
        part_pair += 0.5 * num_part * dt / tau_pair
        num_pairs = int(round(part_pair))
        part_pair -= num_pairs
        select_pairs(particles, num_pairs, num_fl_pairs)

        # Rotate particles
        temp_comp = particles[-1]()
        for i in [i*2 + 1 for i in range(num_pairs - 1)]:
            #particles[-i] = particles[-(i+2)]
            particles[-i](particles[-(i+2)])
        particles[-(num_pairs * 2 - 1)](temp_comp)

        # Now loop over mix-react substeps
        dt_sub = dt / num_substeps
        for i in range(num_substeps):
            mix_substep(particles, dt_sub, tau_mix)
            reaction_substep(particles, time + dt_sub * (i + 1))

        time += dt
        i_step += 1

        # Save mean properties
        temp_mean[i_step] = np.mean([p.gas.T for p in particles])
        times[i_step] = time

        # Save full data
        save_data(i_step, time, particles, particle_data)

        print('{:6.2f}  {:9.1f}'.format(time*1000., temp_mean[i_step]))

    return particle_data


def parse_input(input_file):
    """Parse input file for PaSR operating parameters.

    :param input_file:
        Filename with YAML-format input file.
    """

    with open(input_file, 'r') as f:
        pars = yaml.load(f)

    case = pars.get('case', None)
    if not case in ['premixed', 'non-premixed']:
        print('Error: case needs to be one of '
              '"premixed" or "non-premixed".')
        sys.exit(1)

    if not pars.get('temperature', None):
        print('Error: (initial) temperature needs to be specified.')
        sys.exit(1)

    if not pars.get('pressure', None):
        print('Error: pressure needs to be specified.')
        sys.exit(1)

    eq_ratio = pars.get('equivalence ratio', None)
    if not eq_ratio or eq_ratio < 0.0:
        print('Error: eq_ratio needs to be specified and > 0.0.')
        sys.exit(1)

    if not pars.get('fuel', None):
        print('Error: fuel species and mole fraction need to specified.')
        sys.exit(1)

    if not pars.get('oxidizer', None):
        print('Error: oxidizer species and mole fractions '
              'need to be specified.')
        sys.exit(1)

    if not pars.get('complete products', None):
        print('Error: need to specify list of complete products.')
        sys.exit(1)

    # Optional inputs
    if not pars.get('number of particles', None):
        pars['number of particles'] = 100
    if not pars.get('residence time', None):
        pars['residence time'] = 10.e-3
    if not pars.get('mixing time', None):
        pars['mixing time'] = 1.e-3
    if not pars.get('pairing time', None):
        pars['pairing time'] = 1.e-3
    if not pars.get('number of residence times', None):
        pars['number of residence times'] = 5

    return pars


if __name__ == "__main__":
    parser = ArgumentParser(description='Runs partially stirred reactor '
                                        '(PaSR) simulation.'
                            )
    parser.add_argument('-i', '--input',
                        type=str, required=True,
                        help='Input file in YAML format for PaSR simulation.'
                        )
    parser.add_argument('-m', '--mech',
                        type=str, required=True,
                        help='Mechanism input file in either Cantera or '
                             'Chemkin format.'
                        )
    parser.add_argument('-t', '--thermo',
                        type=str, required=False,
                        help='Thermodynamic input file, optional.'
                        )
    args = parser.parse_args()

    inputs = parse_input(args.input)

    partially_stirred_reactor(args.mech, inputs['case'],
                              inputs['temperature'], inputs['pressure'],
                              inputs['eq_ratio'], inputs['fuel'],
                              inputs['oxidizer'], inputs['complete_products'],
                              inputs['number of particles'],
                              inputs['residence time'], inputs['mixing time'],
                              inputs['pairing time'],
                              inputs['number of residence times']
                              )
