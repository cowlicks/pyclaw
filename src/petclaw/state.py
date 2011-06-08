
import pyclaw.state

class State(pyclaw.state.State):
    r"""  See the corresponding PyClaw class documentation."""
    def meqn():
        doc = r"""(int) - Number of unknowns (components of q)"""
        def fset(self,meqn):
            if self.q_da is not None:
                raise Exception('You cannot change state.meqn after q is initialized.')
            else:
                self.init_q_da(meqn)
        def fget(self):
            if self.q_da is None:
                raise Exception('state.meqn has not been set.')
            else: return self.q_da.dof
        return locals()
    meqn = property(**meqn())
    def maux():
        doc = r"""(int) - Number of auxiliary fields"""
        def fset(self,maux):
            if self.aux_da is not None:
                raise Exception('You cannot change state.maux after aux is initialized.')
            else:
                if maux>0:
                    self.init_aux_da(maux)
        def fget(self):
            if self.aux_da is None: return 0
            else: return self.aux_da.dof
        return locals()
    maux = property(**maux())
    def q():
        def fget(self):
            if self.q_da is None: return 0
            q_dim = self.grid.ng
            q_dim.insert(0,self.meqn)
            q=self.gqVec.getArray().reshape(q_dim, order = 'F')
            return q
        def fset(self,q):
            meqn = q.shape[0]
            if self.gqVec is None: self.init_q_da(meqn)
            self.gqVec.setArray(q.reshape([-1], order = 'F'))
        return locals()
    q = property(**q())
    def aux():
        """
        We never communicate aux values; every processor should set its own ghost cell
        values for the aux array.  The global aux vector is used only for outputting
        the aux values to file; everywhere else we use the local vector.
        """
        def fget(self):
            if self.aux_da is None: return None
            aux_dim = self.grid.ng
            aux_dim.insert(0,self.maux)
            aux=self.gauxVec.getArray().reshape(aux_dim, order = 'F')
            return aux
        def fset(self,aux):
            if self.aux_da is None: 
                maux=aux.shape[0]
                self.init_aux_da(maux)
            self.gauxVec.setArray(aux.reshape([-1], order = 'F'))
        return locals()
    aux = property(**aux())
    def ndim():
        def fget(self):
            return self.grid.ndim
        return locals()
    ndim = property(**ndim())


    def __init__(self,grid):
        r"""
        Here we don't call super because q and aux must be properties in PetClaw
        but should not be properties in PyClaw.

        """
        import petclaw.grid
        if not isinstance(grid,petclaw.grid.Grid):
            raise Exception("""A PetClaw State object must be initialized with
                             a PetClaw Grid object.""")
        self.q_da = None
        self.gqVec = None
        self.lqVec = None

        self.aux_da = None
        self.gauxVec = None
        self.lauxVec = None

        # ========== Attribute Definitions ===================================
        self.grid = grid
        r"""pyclaw.Grid.grid - The grid this state lives on"""
        self.aux_global = {}
        r"""(dict) - Dictionary of global values for this grid, 
            ``default = {}``"""
        self.t=0.
        r"""(float) - Current time represented on this grid, 
            ``default = 0.0``"""
        self.stateno = 1
        r"""(int) - State number of current state, ``default = 1``"""


    def init_aux_da(self,maux,mbc=0):
        r"""
        Initializes PETSc DA for q. It initializes aux_da, gauxVec and lauxVec.
        """
        from petsc4py import PETSc

        if hasattr(PETSc.DA, 'PeriodicType'):
            if self.ndim == 1:
                periodic_type = PETSc.DA.PeriodicType.X
            elif self.ndim == 2:
                periodic_type = PETSc.DA.PeriodicType.XY
            elif self.ndim == 3:
                periodic_type = PETSc.DA.PeriodicType.XYZ
            else:
                raise Exception("Invalid number of dimensions")

            self.aux_da = PETSc.DA().create(dim=self.ndim,
                                            dof=maux, 
                                            sizes=self.grid.n,  
                                            periodic_type = periodic_type,
                                            stencil_width=mbc,
                                            comm=PETSc.COMM_WORLD)
    

        else:
            self.aux_da = PETSc.DA().create(dim=self.ndim,
                                            dof=maux,
                                            sizes=self.grid.n, 
                                            boundary_type = PETSc.DA.BoundaryType.PERIODIC,
                                            stencil_width=mbc,
                                            comm=PETSc.COMM_WORLD)

       
        self.gauxVec = self.aux_da.createGlobalVector()
        self.lauxVec = self.aux_da.createLocalVector()
 

    def init_q_da(self,meqn,mbc=0):
        r"""
        Initializes PETSc structures for q. It initializes q_da, gqVec and lqVec,
        and also sets up nstart, nend, and mbc for the dimensions.
        
        """
        from petsc4py import PETSc

        #Due to the way PETSc works, we just make the grid always periodic,
        #regardless of the boundary conditions actually selected.
        #This works because in solver.qbc() we first call globalToLocal()
        #and then impose the real boundary conditions (if non-periodic).

        if hasattr(PETSc.DA, 'PeriodicType'):
            if self.ndim == 1:
                periodic_type = PETSc.DA.PeriodicType.X
            elif self.ndim == 2:
                periodic_type = PETSc.DA.PeriodicType.XY
            elif self.ndim == 3:
                periodic_type = PETSc.DA.PeriodicType.XYZ
            else:
                raise Exception("Invalid number of dimensions")
            self.q_da = PETSc.DA().create(dim=self.ndim,
                                          dof=meqn,
                                          sizes=self.grid.n, 
                                          periodic_type = periodic_type,
                                          #stencil_type=self.STENCIL,
                                          stencil_width=mbc,
                                          comm=PETSc.COMM_WORLD)

        else:
            self.q_da = PETSc.DA().create(dim=self.ndim,
                                          dof=meqn,
                                          sizes=self.grid.n, 
                                          boundary_type = PETSc.DA.BoundaryType.PERIODIC,
                                          #stencil_type=self.STENCIL,
                                          stencil_width=mbc,
                                          comm=PETSc.COMM_WORLD)

        self.gqVec = self.q_da.createGlobalVector()
        self.lqVec = self.q_da.createLocalVector()

        #Now set up the local indices:
        ranges = self.q_da.getRanges()
        for i,nrange in enumerate(ranges):
            self.grid.dimensions[i].nstart=nrange[0]
            self.grid.dimensions[i].nend  =nrange[1]

    def set_stencil_width(self,mbc):
        r"""
        This is a hack to deal with the fact that petsc4py
        doesn't allow us to change the stencil_width (mbc).

        Instead, we initially create DAs with stencil_width=0.
        Then, in solver.setup(), we call this function to replace
        those DAs with new ones that have the right stencil width.
        """

        q0 = self.q.copy()
        self.init_q_da(self.meqn,mbc)
        self.q = q0

        if self.aux is not None:
            aux0 = self.aux.copy()
            self.init_aux_da(self.maux,mbc)
            self.aux = aux0
