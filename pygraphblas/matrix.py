
from .base import lib, ffi, _check, _gb_from_type
from .vector import Vector

class Matrix:

    def __init__(self, matrix):
        self.matrix = matrix

    def __del__(self):
        _check(lib.GrB_Matrix_free(self.matrix))

    @classmethod
    def from_type(cls, py_type, nrows=0, ncols=0):
        new_mat = ffi.new('GrB_Matrix*')
        gb_type = _gb_from_type(py_type)
        _check(lib.GrB_Matrix_new(new_mat, gb_type, nrows, ncols))
        return cls(new_mat)

    @classmethod
    def dup(cls, mat):
        new_mat = ffi.new('GrB_Matrix*')
        _check(lib.GrB_Matrix_dup(new_mat, mat.matrix[0]))
        return cls(new_mat)

    @classmethod
    def from_edgelists(cls, I, J, V, nrows=None, ncols=None):
        if not nrows:
            nrows = len(I)
        if not ncols:
            ncols = len(J)
        # TODO use ffi and GrB_Matrix_build
        m = cls.from_type(int, nrows, ncols)
        for i, j, v in zip(I, J, V):
            m[i, j] = v
        return m

    @property
    def gb_type(self):
        new_type = ffi.new('GrB_Type*')
        _check(lib.GxB_Matrix_type(new_type, self.matrix[0]))
        return new_type[0]

    @property
    def nrows(self):
        n = ffi.new('GrB_Index*')
        _check(lib.GrB_Matrix_ncols(n, self.matrix[0]))
        return n[0]

    @property
    def ncols(self):
        n = ffi.new('GrB_Index*')
        _check(lib.GrB_Matrix_nrows(n, self.matrix[0]))
        return n[0]

    @property
    def nvals(self):
        n = ffi.new('GrB_Index*')
        _check(lib.GrB_Matrix_nvals(n, self.matrix[0]))
        return n[0]

    def clear(self):
        _check(lib.GrB_Matrix_clear(self.matrix[0]))

    def resize(self, nrows, ncols):
        _check(lib.GxB_Matrix_resize(
            self.matrix[0],
            nrows,
            ncols))

    def build_range(self, rslice, stop_val):
        if rslice is None or (rslice.start is None and rslice.stop is None and rslice.step is None):
            return lib.GrB_ALL, 0
        if rslice.start is None:
            rslice.start = 0
        if rslice.stop is None:
            rslice.stop = stop_val
        if rslice.step is None:
            I = ffi.new('GrB_Index[2]',
                        [rslice.start, rslice.stop])
            ni = lib.GxB_RANGE
        else:
            I = ffi.new('GrB_Index[3]',
                        [rslice.start, rslice.step, rslice.stop])
            ni = lib.GxB_STRIDE
        return I, ni

    def slice_matrix(self, rindex=slice(None), cindex=slice(None), trans=False):
        desc = ffi.new('GrB_Descriptor*')
        if row:
            # transpose input to get row
            _check(lib.GrB_Descriptor_new(desc))
            _check(lib.GrB_Descriptor_set(
                desc[0],
                lib.GrB_INP0,
                lib.GrB_TRAN))
        else:
            desc[0] = ffi.NULL

        if isinstance(rindex, slice):
            I, ni = self.build_range(rindex, self.nrows)
        elif isinstance(rindex, int):
            pass
        if isinstance(cindex, slice):
            J, nj = self.build_range(cindex, self.ncols)
        elif isinstance(cindex, int):
            pass

    def slice_vector(self, index, vslice=None, transpose=False):
        desc = ffi.new('GrB_Descriptor*')
        if transpose:
            # transpose input to get row
            _check(lib.GrB_Descriptor_new(desc))
            _check(lib.GrB_Descriptor_set(
                desc[0],
                lib.GrB_INP0,
                lib.GrB_TRAN))
        else:
            desc[0] = ffi.NULL

        # if vslice is not None:
        #     if vslice.start is None:
        #         vslice.start = 0
        #     if vslice.stop is None:
        #         if row:
        #             vslice.stop = self.nrows
        #         else:
        #             vslice.stop = self.ncols
        #     if vslice.step is None:
        #         I = ffi.new('GrB_Index[2]',
        #                     [rindex.start, rindex.stop])
        #         ni = lib.GxB_RANGE
        #     else:
        #         I = ffi.new('GrB_Index[3]',
        #                     [rindex.start, rindex.step, rindex.stop])
        #         ni = lib.GxB_STRIDE
        # else:
        #     I = lib.GrB_ALL
        #     ni = 0

        new_vec = ffi.new('GrB_Vector*')
        _check(lib.GrB_Vector_new(
            new_vec,
            self.gb_type,
            self.ncols))

        I, ni = self.build_range(vslice, self.nrows if transpose else self.ncols)

        _check(lib.GrB_Col_extract(
            new_vec[0],
            ffi.NULL,
            ffi.NULL,
            self.matrix[0],
            I,
            ni,
            index,
            desc[0]
            ))
        return Vector(new_vec)

    def __getitem__(self, index):
        if isinstance(index, int):
            # a[3] extract row vector
            return self.slice_vector(index, None, True)
        if isinstance(index, slice):
            # a[:] submatrix of rows
            return self.slice_matrix(index)

        if not isinstance(index, (tuple, list)):
            raise TypeError

        i0 = index[0]
        i1 = index[1]
        if isinstance(i0, int) and isinstance(i1, int):
            # a[3,3] extract single element
            result = ffi.new('int64_t*')
            _check(lib.GrB_Matrix_extractElement_INT64(
                result,
                self.matrix[0],
                index[0],
                index[1]))
            return result[0]

        if isinstance(i1, int) and isinstance(i1, (slice, tuple)):
            # a[3,:] extract slice of row vector
            return
        if isinstance(i1, (slice, tuple)) and isinstance(i1, int):
            # a[:,3] extract slice of col vector
            return
        if isinstance(i0, (slice, tuple)) and isinstance(i1, (slice, tuple)):
            # a[:,:] extract submatrix
            return

    def __setitem__(self, index, value):
        if isinstance(index, (int, slice)):
            return # TODO set row vector
        if isinstance(index, tuple):
            if isinstance(index[0], int) and isinstance(index[1], int):
                _check(lib.GrB_Matrix_setElement_INT64(
                    self.matrix[0],
                    ffi.cast('int64_t', value),
                    index[0],
                    index[1]))

    def __repr__(self):
        return '<Matrix (%sx%s: %s)>' % (
            self.nrows,
            self.ncols,
            self.nvals)
