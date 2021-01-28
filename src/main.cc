#include "arg_parse.h"
#include "probability_util.h"
#include "simulators/frame_simulator.h"
#include "simulators/tableau_simulator.h"

std::vector<const char *> known_arguments{
    "-shots",
    "-frame0",
    "-repl",
    "-format",
    "-out",
};
std::vector<const char *> format_names{
    "01",
    "b8",
    "ptb64",
};
std::vector<SampleFormat> format_values{
        SAMPLE_FORMAT_01,
        SAMPLE_FORMAT_B8,
        SAMPLE_FORMAT_PTB64,
};

int main(int argc, const char **argv) {
    check_for_unknown_arguments(known_arguments.size(), known_arguments.data(), argc, argv);

    SampleFormat format = format_values[find_enum_argument(
        "-format", SAMPLE_FORMAT_01, format_names.size(), format_names.data(), argc, argv)];
    bool interactive = find_bool_argument("-repl", argc, argv);
    bool frame0 = find_bool_argument("-frame0", argc, argv);
    int samples = (size_t)find_int_argument("-shots", 1, 0, 1 << 30, argc, argv);
    const char *out_path = find_argument("-out", argc, argv);
    FILE *out;
    if (out_path == nullptr) {
        out = stdout;
    } else {
        out = fopen(out_path, "w");
        if (out == nullptr) {
            std::cerr << "Failed to open '" << out_path << "' to write.";
            exit(EXIT_FAILURE);
        }
    }

    if (samples != 1 && interactive) {
        std::cerr << "Incompatible arguments. Multiple samples and interactive.\n";
        exit(EXIT_FAILURE);
    }
    if (interactive && format != SAMPLE_FORMAT_01) {
        std::cerr << "Incompatible arguments. Binary output format and repl.\n";
        exit(EXIT_FAILURE);
    }
    if (interactive && frame0) {
        std::cerr << "Incompatible arguments. -repl and -frame0.\n";
        exit(EXIT_FAILURE);
    }

    std::mt19937_64 rng = externally_seeded_rng();
    if (frame0) {
        auto circuit = Circuit::from_file(stdin);
        simd_bits ref(circuit.num_measurements);
        FrameSimulator::sample_out(circuit, ref, samples, out, format, rng);
    } else if (samples == 1 && format == SAMPLE_FORMAT_01) {
        TableauSimulator::sample_stream(stdin, out, interactive, rng);
    } else {
        auto circuit = Circuit::from_file(stdin);
        auto ref = TableauSimulator::reference_sample_circuit(circuit);
        FrameSimulator::sample_out(circuit, ref, samples, out, format, rng);
    }
}
