import numpy as np
import numpy
import unittest

import theano
from theano.tests import unittest_tools as utt

from theano.tensor.extra_ops import (CumsumOp, cumsum, CumprodOp, cumprod,
                                     BinCountOp, bincount, DiffOp, diff,
                                     squeeze, RepeatOp, repeat,
                                     Bartlett, bartlett,
                                     FillDiagonal, fill_diagonal,
                                     FillDiagonalOffset, fill_diagonal_offset,
                                     to_one_hot)
from theano import tensor as T
from theano import config, tensor, function


numpy_ver = [int(n) for n in numpy.__version__.split('.')[:2]]
numpy_16 = bool(numpy_ver >= [1, 6])


class TestCumsumOp(utt.InferShapeTester):

    def setUp(self):
        super(TestCumsumOp, self).setUp()
        self.op_class = CumsumOp
        self.op = CumsumOp()

    def test_cumsumOp(self):
        x = T.tensor3('x')
        a = np.random.random((3, 5, 2)).astype(config.floatX)

        # Test axis out of bounds
        self.assertRaises(ValueError, cumsum, x, axis=3)
        self.assertRaises(ValueError, cumsum, x, axis=-4)

        f = theano.function([x], cumsum(x))
        assert np.allclose(np.cumsum(a), f(a))  # Test axis=None

        for axis in range(-len(a.shape), len(a.shape)):
            f = theano.function([x], cumsum(x, axis=axis))
            assert np.allclose(np.cumsum(a, axis=axis), f(a))

    def test_infer_shape(self):
        x = T.tensor3('x')
        a = np.random.random((3, 5, 2)).astype(config.floatX)

        # Test axis=None
        self._compile_and_check([x],
                                [self.op(x)],
                                [a],
                                self.op_class)

        for axis in range(-len(a.shape), len(a.shape)):
            self._compile_and_check([x],
                                    [cumsum(x, axis=axis)],
                                    [a],
                                    self.op_class)

    def test_grad(self):
        a = np.random.random((3, 5, 2)).astype(config.floatX)

        utt.verify_grad(self.op, [a])  # Test axis=None

        for axis in range(-len(a.shape), len(a.shape)):
            utt.verify_grad(self.op_class(axis=axis), [a], eps=4e-4)


class TestCumprodOp(utt.InferShapeTester):

    def setUp(self):
        super(TestCumprodOp, self).setUp()
        self.op_class = CumprodOp
        self.op = CumprodOp()

    def test_CumprodOp(self):
        x = T.tensor3('x')
        a = np.random.random((3, 5, 2)).astype(config.floatX)

        # Test axis out of bounds
        self.assertRaises(ValueError, cumprod, x, axis=3)
        self.assertRaises(ValueError, cumprod, x, axis=-4)

        f = theano.function([x], cumprod(x))
        assert np.allclose(np.cumprod(a), f(a))  # Test axis=None

        for axis in range(-len(a.shape), len(a.shape)):
            f = theano.function([x], cumprod(x, axis=axis))
            assert np.allclose(np.cumprod(a, axis=axis), f(a))

    def test_infer_shape(self):
        x = T.tensor3('x')
        a = np.random.random((3, 5, 2)).astype(config.floatX)

        # Test axis=None
        self._compile_and_check([x],
                                [self.op(x)],
                                [a],
                                self.op_class)

        for axis in range(-len(a.shape), len(a.shape)):
            self._compile_and_check([x],
                                    [cumprod(x, axis=axis)],
                                    [a],
                                    self.op_class)

    def test_grad(self):
        a = np.random.random((3, 5, 2)).astype(config.floatX)

        utt.verify_grad(self.op, [a])  # Test axis=None

        for axis in range(-len(a.shape), len(a.shape)):
            utt.verify_grad(self.op_class(axis=axis), [a])


class TestBinCountOp(utt.InferShapeTester):
    def setUp(self):
        super(TestBinCountOp, self).setUp()
        self.op_class = BinCountOp
        self.op = BinCountOp()

    def test_bincountFn(self):
        w = T.vector('w')
        for dtype in ('int8', 'int16', 'int32', 'int64',
                      'uint8', 'uint16', 'uint32', 'uint64'):
            x = T.vector('x', dtype=dtype)

            # uint64 always fails
            if dtype in ('uint64',):
                self.assertRaises(TypeError, bincount, x)

            else:
                a = np.random.random_integers(50, size=(25)).astype(dtype)
                weights = np.random.random((25,)).astype(config.floatX)

                f1 = theano.function([x], bincount(x))
                f2 = theano.function([x, w], bincount(x, weights=w))

                assert (np.bincount(a) == f1(a)).all()
                assert np.allclose(np.bincount(a, weights=weights),
                                   f2(a, weights))
                f3 = theano.function([x], bincount(x, minlength=23))
                f4 = theano.function([x], bincount(x, minlength=5))
                assert (np.bincount(a, minlength=23) == f3(a)).all()
                assert (np.bincount(a, minlength=5) == f4(a)).all()
                # skip the following test when using unsigned ints
                if not dtype.startswith('u'):
                    a[0] = -1
                    f5 = theano.function([x], bincount(x, assert_nonneg=True))
                    self.assertRaises(AssertionError, f5, a)

    def test_bincountOp(self):
        w = T.vector('w')
        for dtype in ('int8', 'int16', 'int32', 'int64',
                      'uint8', 'uint16', 'uint32', 'uint64'):
            # uint64 always fails
            # int64 and uint32 also fail if python int are 32-bit
            int_bitwidth = theano.gof.python_int_bitwidth()
            if int_bitwidth == 64:
                numpy_unsupported_dtypes = ('uint64',)
            if int_bitwidth == 32:
                numpy_unsupported_dtypes = ('uint32', 'int64', 'uint64')

            x = T.vector('x', dtype=dtype)

            if dtype in numpy_unsupported_dtypes:
                self.assertRaises(TypeError, BinCountOp(), x)

            else:
                a = np.random.random_integers(50, size=(25)).astype(dtype)
                weights = np.random.random((25,)).astype(config.floatX)

                f1 = theano.function([x], BinCountOp()(x, weights=None))
                f2 = theano.function([x, w], BinCountOp()(x, weights=w))

                assert (np.bincount(a) == f1(a)).all()
                assert np.allclose(np.bincount(a, weights=weights),
                                   f2(a, weights))
                if not numpy_16:
                    continue
                f3 = theano.function([x], BinCountOp(minlength=23)(x, weights=None))
                f4 = theano.function([x], BinCountOp(minlength=5)(x, weights=None))
                assert (np.bincount(a, minlength=23) == f3(a)).all()
                assert (np.bincount(a, minlength=5) == f4(a)).all()

    def test_infer_shape(self):
        for dtype in tensor.discrete_dtypes:
            # uint64 always fails
            # int64 and uint32 also fail if python int are 32-bit
            int_bitwidth = theano.gof.python_int_bitwidth()
            if int_bitwidth == 64:
                numpy_unsupported_dtypes = ('uint64',)
            if int_bitwidth == 32:
                numpy_unsupported_dtypes = ('uint32', 'int64', 'uint64')

            x = T.vector('x', dtype=dtype)

            if dtype in numpy_unsupported_dtypes:
                self.assertRaises(TypeError, BinCountOp(), x)

            else:
                self._compile_and_check(
                        [x],
                        [BinCountOp()(x,None)],
                        [np.random.random_integers(
                            50, size=(25,)).astype(dtype)],
                        self.op_class)

                weights = np.random.random((25,)).astype(config.floatX)
                self._compile_and_check(
                        [x],
                        [BinCountOp()(x, weights=weights)],
                        [np.random.random_integers(
                            50, size=(25,)).astype(dtype)],
                        self.op_class)

                if not numpy_16:
                    continue
                self._compile_and_check(
                        [x],
                        [BinCountOp(minlength=60)(x, weights=weights)],
                        [np.random.random_integers(
                            50, size=(25,)).astype(dtype)],
                        self.op_class)

                self._compile_and_check(
                        [x],
                        [BinCountOp(minlength=5)(x, weights=weights)],
                        [np.random.random_integers(
                            50, size=(25,)).astype(dtype)],
                        self.op_class)


class TestDiffOp(utt.InferShapeTester):
    nb = 10  # Number of time iterating for n

    def setUp(self):
        super(TestDiffOp, self).setUp()
        self.op_class = DiffOp
        self.op = DiffOp()

    def test_diffOp(self):
        x = T.matrix('x')
        a = np.random.random((30, 50)).astype(config.floatX)

        f = theano.function([x], diff(x))
        assert np.allclose(np.diff(a), f(a))

        for axis in range(len(a.shape)):
            for k in range(TestDiffOp.nb):
                g = theano.function([x], diff(x, n=k, axis=axis))
                assert np.allclose(np.diff(a, n=k, axis=axis), g(a))

    def test_infer_shape(self):
        x = T.matrix('x')
        a = np.random.random((30, 50)).astype(config.floatX)

        self._compile_and_check([x],
                                [self.op(x)],
                                [a],
                                self.op_class)

        for axis in range(len(a.shape)):
            for k in range(TestDiffOp.nb):
                self._compile_and_check([x],
                                        [diff(x, n=k, axis=axis)],
                                        [a],
                                        self.op_class)

    def test_grad(self):
        x = T.vector('x')
        a = np.random.random(50).astype(config.floatX)

        theano.function([x], T.grad(T.sum(diff(x)), x))
        utt.verify_grad(self.op, [a])

        for k in range(TestDiffOp.nb):
            theano.function([x], T.grad(T.sum(diff(x, n=k)), x))
            utt.verify_grad(DiffOp(n=k), [a], eps=7e-3)


class SqueezeTester(utt.InferShapeTester):
    shape_list = [(1, 3),
                  (1, 2, 3),
                  (1, 5, 1, 1, 6)]
    broadcast_list = [[True, False],
                      [True, False, False],
                      [True, False, True, True, False]]

    def setUp(self):
        super(SqueezeTester, self).setUp()
        self.op = squeeze

    def test_op(self):
        for shape, broadcast in zip(self.shape_list, self.broadcast_list):
            data = numpy.random.random(size=shape).astype(theano.config.floatX)
            variable = tensor.TensorType(theano.config.floatX, broadcast)()

            f = theano.function([variable], self.op(variable))

            expected = numpy.squeeze(data)
            tested = f(data)

            assert tested.shape == expected.shape
            assert numpy.allclose(tested, expected)

    def test_infer_shape(self):
        for shape, broadcast in zip(self.shape_list, self.broadcast_list):
            data = numpy.random.random(size=shape).astype(theano.config.floatX)
            variable = tensor.TensorType(theano.config.floatX, broadcast)()

            self._compile_and_check([variable],
                                    [self.op(variable)],
                                    [data],
                                    tensor.DimShuffle,
                                    warn=False)

    def test_grad(self):
        for shape, broadcast in zip(self.shape_list, self.broadcast_list):
            data = numpy.random.random(size=shape).astype(theano.config.floatX)

            utt.verify_grad(self.op, [data])

    def test_var_interface(self):
        # same as test_op, but use a_theano_var.squeeze.
        for shape, broadcast in zip(self.shape_list, self.broadcast_list):
            data = numpy.random.random(size=shape).astype(theano.config.floatX)
            variable = tensor.TensorType(theano.config.floatX, broadcast)()

            f = theano.function([variable], variable.squeeze())

            expected = numpy.squeeze(data)
            tested = f(data)

            assert tested.shape == expected.shape
            assert numpy.allclose(tested, expected)


class TestRepeatOp(utt.InferShapeTester):
    def _possible_axis(self, ndim):
        return [None] + range(ndim) + [-i for i in range(ndim)]

    def setUp(self):
        super(TestRepeatOp, self).setUp()
        self.op_class = RepeatOp
        self.op = RepeatOp()
        # uint64 always fails
        # int64 and uint32 also fail if python int are 32-bit
        ptr_bitwidth = theano.gof.local_bitwidth()
        if ptr_bitwidth == 64:
            self.numpy_unsupported_dtypes = ('uint64',)
        if ptr_bitwidth == 32:
            self.numpy_unsupported_dtypes = ('uint32', 'int64', 'uint64')

    def test_repeatOp(self):
        for ndim in range(3):
            x = T.TensorType(config.floatX, [False] * ndim)()
            a = np.random.random((10, ) * ndim).astype(config.floatX)

            for axis in self._possible_axis(ndim):
                for dtype in tensor.discrete_dtypes:
                    r_var = T.scalar(dtype=dtype)
                    r = numpy.asarray(3, dtype=dtype)
                    if dtype in self.numpy_unsupported_dtypes:
                        self.assertRaises(TypeError,
                                repeat, x, r_var, axis=axis)
                    else:
                        f = theano.function([x, r_var],
                                            repeat(x, r_var, axis=axis))
                        assert np.allclose(np.repeat(a, r, axis=axis),
                                           f(a, r))

                        r_var = T.vector(dtype=dtype)
                        if axis is None:
                            r = np.random.random_integers(
                                    5, size=a.size).astype(dtype)
                        else:
                            r = np.random.random_integers(
                                    5, size=(10,)).astype(dtype)

                        f = theano.function([x, r_var],
                                            repeat(x, r_var, axis=axis))
                        assert np.allclose(np.repeat(a, r, axis=axis),
                                           f(a, r))

    def test_infer_shape(self):
        for ndim in range(4):
            x = T.TensorType(config.floatX, [False] * ndim)()
            shp = (numpy.arange(ndim) + 1) * 5
            a = np.random.random(shp).astype(config.floatX)

            for axis in self._possible_axis(ndim):
                for dtype in tensor.discrete_dtypes:
                    r_var = T.scalar(dtype=dtype)
                    r = numpy.asarray(3, dtype=dtype)
                    if dtype in self.numpy_unsupported_dtypes:
                        self.assertRaises(TypeError, repeat, x, r_var)
                    else:
                        self._compile_and_check(
                                [x, r_var],
                                [RepeatOp(axis=axis)(x, r_var)],
                                [a, r],
                                self.op_class)

                        r_var = T.vector(dtype=dtype)
                        if axis is None:
                            r = np.random.random_integers(
                                    5, size=a.size).astype(dtype)
                        elif a.size > 0:
                            r = np.random.random_integers(
                                    5, size=a.shape[axis]).astype(dtype)
                        else:
                            r = np.random.random_integers(
                                    5, size=(10,)).astype(dtype)

                        self._compile_and_check(
                                [x, r_var],
                                [RepeatOp(axis=axis)(x, r_var)],
                                [a, r],
                                self.op_class)

    def test_grad(self):
        for ndim in range(3):
            a = np.random.random((10, ) * ndim).astype(config.floatX)

            for axis in self._possible_axis(ndim):
                utt.verify_grad(lambda x: RepeatOp(axis=axis)(x, 3), [a])

    def test_broadcastable(self):
        x = T.TensorType(config.floatX, [False, True, False])()
        r = RepeatOp(axis=1)(x, 2)
        self.assertEqual(r.broadcastable, (False, False, False))
        r = RepeatOp(axis=1)(x, 1)
        self.assertEqual(r.broadcastable, (False, True, False))
        r = RepeatOp(axis=0)(x, 2)
        self.assertEqual(r.broadcastable, (False, True, False))


class TestBartlett(utt.InferShapeTester):

    def setUp(self):
        super(TestBartlett, self).setUp()
        self.op_class = Bartlett
        self.op = bartlett

    def test_perform(self):
        x = tensor.lscalar()
        f = function([x], self.op(x))
        M = numpy.random.random_integers(3, 50, size=())
        assert numpy.allclose(f(M), numpy.bartlett(M))
        assert numpy.allclose(f(0), numpy.bartlett(0))
        assert numpy.allclose(f(-1), numpy.bartlett(-1))
        b = numpy.array([17], dtype='uint8')
        assert numpy.allclose(f(b[0]), numpy.bartlett(b[0]))

    def test_infer_shape(self):
        x = tensor.lscalar()
        self._compile_and_check([x], [self.op(x)],
                                [numpy.random.random_integers(3, 50, size=())],
                                self.op_class)
        self._compile_and_check([x], [self.op(x)], [0], self.op_class)
        self._compile_and_check([x], [self.op(x)], [1], self.op_class)


class TestFillDiagonal(utt.InferShapeTester):

    rng = numpy.random.RandomState(43)

    def setUp(self):
        super(TestFillDiagonal, self).setUp()
        self.op_class = FillDiagonal
        self.op = fill_diagonal

    def test_perform(self):
        x = tensor.matrix()
        y = tensor.scalar()
        f = function([x, y], fill_diagonal(x, y))
        for shp in [(8, 8), (5, 8), (8, 5)]:
            a = numpy.random.rand(*shp).astype(config.floatX)
            val = numpy.cast[config.floatX](numpy.random.rand())
            out = f(a, val)
            # We can't use numpy.fill_diagonal as it is bugged.
            assert numpy.allclose(numpy.diag(out), val)
            assert (out == val).sum() == min(a.shape)

        # test for 3d tensor
        a = numpy.random.rand(3, 3, 3).astype(config.floatX)
        x = tensor.tensor3()
        y = tensor.scalar()
        f = function([x, y], fill_diagonal(x, y))
        val = numpy.cast[config.floatX](numpy.random.rand() + 10)
        out = f(a, val)
        # We can't use numpy.fill_diagonal as it is bugged.
        assert out[0, 0, 0] == val
        assert out[1, 1, 1] == val
        assert out[2, 2, 2] == val
        assert (out == val).sum() == min(a.shape)

    def test_gradient(self):
        utt.verify_grad(fill_diagonal, [numpy.random.rand(5, 8),
                                        numpy.random.rand()],
                        n_tests=1, rng=TestFillDiagonal.rng)
        utt.verify_grad(fill_diagonal, [numpy.random.rand(8, 5),
                                        numpy.random.rand()],
                        n_tests=1, rng=TestFillDiagonal.rng)

    def test_infer_shape(self):
        z = tensor.dtensor3()
        x = tensor.dmatrix()
        y = tensor.dscalar()
        self._compile_and_check([x, y], [self.op(x, y)],
                                [numpy.random.rand(8, 5),
                                 numpy.random.rand()],
                                self.op_class)
        self._compile_and_check([z, y], [self.op(z, y)],
                                # must be square when nd>2
                                [numpy.random.rand(8, 8, 8),
                                 numpy.random.rand()],
                                self.op_class,
                                warn=False)


class TestFillDiagonalOffset(utt.InferShapeTester):

    rng = numpy.random.RandomState(43)

    def setUp(self):
        super(TestFillDiagonalOffset, self).setUp()
        self.op_class = FillDiagonalOffset
        self.op = fill_diagonal_offset

    def test_perform(self):
        x = tensor.matrix()
        y = tensor.scalar()
        z = tensor.iscalar()

        f = function([x, y, z], fill_diagonal_offset(x, y, z))
        for test_offset in (-5, -4, -1, 0, 1, 4, 5):
            for shp in [(8, 8), (5, 8), (8, 5), (5, 5)]:
                a = numpy.random.rand(*shp).astype(config.floatX)
                val = numpy.cast[config.floatX](numpy.random.rand())
                out = f(a, val, test_offset)
                # We can't use numpy.fill_diagonal as it is bugged.
                assert numpy.allclose(numpy.diag(out, test_offset), val)
                if test_offset >= 0:
                   assert (out == val).sum() == min( min(a.shape),
                                            a.shape[1]-test_offset )
                else:
                    assert (out == val).sum() == min( min(a.shape),
                                            a.shape[0]+test_offset )

    def test_gradient(self):
        for test_offset in (-5, -4, -1, 0, 1, 4, 5):
            # input 'offset' will not be tested
            def fill_diagonal_with_fix_offset( a, val):
                return fill_diagonal_offset( a, val, test_offset)

            utt.verify_grad(fill_diagonal_with_fix_offset,
                        [numpy.random.rand(5, 8), numpy.random.rand()],
                            n_tests=1, rng=TestFillDiagonalOffset.rng)
            utt.verify_grad(fill_diagonal_with_fix_offset,
                        [numpy.random.rand(8, 5), numpy.random.rand()],
                            n_tests=1, rng=TestFillDiagonalOffset.rng)
            utt.verify_grad(fill_diagonal_with_fix_offset,
                        [numpy.random.rand(5, 5), numpy.random.rand()],
                            n_tests=1, rng=TestFillDiagonalOffset.rng)

    def test_infer_shape(self):
        x = tensor.dmatrix()
        y = tensor.dscalar()
        z = tensor.iscalar()
        for test_offset in (-5, -4, -1, 0, 1, 4, 5):
            self._compile_and_check([x, y, z], [self.op(x, y, z)],
                                    [numpy.random.rand(8, 5),
                                     numpy.random.rand(),
                                     test_offset],
                                     self.op_class )
            self._compile_and_check([x, y, z], [self.op(x, y, z)],
                                    [numpy.random.rand(5, 8),
                                     numpy.random.rand(),
                                     test_offset],
                                     self.op_class )


def test_to_one_hot():
    v = theano.tensor.ivector()
    o = to_one_hot(v, 10)
    f = theano.function([v], o)
    out = f([1, 2, 3, 5, 6])
    assert out.dtype == theano.config.floatX
    assert numpy.allclose(
        out,
        [[0., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
         [0., 0., 1., 0., 0., 0., 0., 0., 0., 0.],
         [0., 0., 0., 1., 0., 0., 0., 0., 0., 0.],
         [0., 0., 0., 0., 0., 1., 0., 0., 0., 0.],
         [0., 0., 0., 0., 0., 0., 1., 0., 0., 0.]])

    v = theano.tensor.ivector()
    o = to_one_hot(v, 10, dtype="int32")
    f = theano.function([v], o)
    out = f([1, 2, 3, 5, 6])
    assert out.dtype == "int32"
    assert numpy.allclose(
        out,
        [[0., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
         [0., 0., 1., 0., 0., 0., 0., 0., 0., 0.],
         [0., 0., 0., 1., 0., 0., 0., 0., 0., 0.],
         [0., 0., 0., 0., 0., 1., 0., 0., 0., 0.],
         [0., 0., 0., 0., 0., 0., 1., 0., 0., 0.]])
