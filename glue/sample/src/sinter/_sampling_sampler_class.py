from typing import Tuple
import abc
import pathlib

import numpy as np
import stim


class CompiledSampler(metaclass=abc.ABCMeta):
    """Abstract class for samplers preconfigured to a specific sampling task.

    This is the type returned by `sinter.Sampler.compile_sampler_for_circuit`. The
    idea is that, when many shots of the same sampling task are going to be
    performed, it is valuable to pay the cost of configuring the sampler only
    once instead of once per batch of shots. Custom samplers can optionally
    implement that method, and return this type, to increase sampling
    efficiency.
    """
    @abc.abstractmethod
    def sample_detectors_bit_packed(
        self,
        *,
        shots: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Samples detectors and observables.
        
        All data returned must be bit packed with bitorder='little'.
        
        Args:
            shots: The number of shots to sample.
            
        Returns:
            Bit packed detector data and bit packed observable flip data stored as
            a tuple of two bit packed numpy arrays. The numpy array must have the 
            following dtype/shape:
            
                dtype: uint8
                shape: (shots, ceil(num_bits_per_shot / 8))
            
            where `num_bits_per_shot` is `circuit.num_detectors` for the detector
            data and `circuit.num_observables` for the observable flip data for the
            circuit this instance was compiled to sample.
        """
        pass


class Sampler(metaclass=abc.ABCMeta):
    """Abstract base class for custom samplers.
    
    Custom samplers can be explained to sinter by inheriting from this class and
    implementing its methods.

    Sampler classes MUST be serializable (e.g. via pickling), so that they can
    be given to worker processes when using python multiprocessing.
    """
    def compile_sampler_for_circuit(
        self,
        *,
        circuit: stim.Circuit,
    ) -> CompiledSampler:
        """Compiles a sampler for the given circuit.
        
        This method is optional to implement. By default, it will raise a
        NotImplementedError. When sampling, sinter will attempt to use this
        method first and otherwise fallback to using `sample_detectors_via_files`.

        The idea is that the preconfigured sampler amortizes the cost of
        configuration over more calls. This makes smaller batch sizes efficient,
        reducing the amount of memory used for storing each batch, improving
        overall efficiency.

        Args:
            circuit: A circuit for the sampler to be configured and sample from.

        Returns:
            An instance of `sinter.CompiledSampler` that can be used to invoke
            the preconfigured sampler.

        Raises:
            NotImplementedError: This `sinter.Sampler` doesn't support compiling
                for a circuit.
        """
        raise NotImplementedError("compile_sampler_for_circuit")

    @abc.abstractmethod
    def sample_detectors_via_files(
        self,
        *,
        shots: int,
        circuit_path: pathlib.Path,
        dets_b8_out_path: pathlib.Path,
        obs_flips_b8_out_path: pathlib.Path,
        tmp_dir: pathlib.Path,
    ) -> None:
        """Performs sampling by reading/writing circuit and data from/to disk.

        Args:
            shots: The number of shots to sample.
            circuit_path: The file path where the circuit should be read from, 
                e.g. using `stim.Circuit.from_file`. The circuit should be used
                to configure the sampler.
            dets_b8_out_path: The file path that detection event data should be
                write to. Note that the file may be a named pipe instead of a
                fixed size object. The detection events will be in b8 format
                (see
                https://github.com/quantumlib/Stim/blob/main/doc/result_formats.md
                ). The number of detection events per shot is available via the
                circuit at `circuit_path`.
            obs_flips_b8_out_path: The file path that observable flip data should
                be write to. Note that the file may be a named pipe instead of a
                fixed size object. The observables will be in b8 format
                (see
                https://github.com/quantumlib/Stim/blob/main/doc/result_formats.md
                ). The number of observables per shot is available via the
                circuit at `circuit_path`.
            tmp_dir: Any temporary files generated by the sampler during its
                operation MUST be put into this directory. The reason for this
                requirement is because sinter is allowed to kill the sampling
                process without warning, without giving it time to clean up any
                temporary objects. All cleanup should be done via sinter
                deleting this directory after killing the sampler.
        """
        pass