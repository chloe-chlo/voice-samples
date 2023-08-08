import argparse
import json
import os
import re
import shutil

DIMENSIONS = ('Pitch', 'Resonance', 'Weight')

LEVEL_NAME_TO_NUMBER = {
    "Higher": 70,
    "Medium": 50,
    "Lower": 30,
}

TERM_MAPPING = {
    "Pitch": {
        "High": "Higher",
        "Medium": "Medium",
        "Low": "Lower",
    },
    "Resonance": {
        "Bright": "Higher",
        "Neutral": "Medium",
        "Dark": "Lower",
    },
    "Weight": {
        "Thin": "Lower",
        "Thick": "Medium",
        "Thicker": "Higher",
    }
}


class Metadata(object):
    def __init__(self, metadata=None, output_dir_components=None):
        self.metadata = {} if metadata is None else metadata
        self.output_dir_components = [] if output_dir_components is None else output_dir_components

    def clone_with(self, new_metadata=None, new_output_dirname_components=None):
        metadata = dict(self.metadata)
        new_metadata = {} if new_metadata is None else new_metadata
        for key, val in new_metadata.items():
            metadata[key] = val
        output_dir_components = list(self.output_dir_components)
        if new_output_dirname_components:
            output_dir_components.extend(new_output_dirname_components)
        return Metadata(metadata=metadata, output_dir_components=output_dir_components)


def extract_dimension_level_string(filename, dimension):
    pattern = r"^(\w+) " + re.escape(dimension) + r"\.wav$"
    match = re.search(pattern, filename)
    if match:
        return match.group(1)
    else:
        raise Exception(
            f"Unrecognized sample filename: {filename}. looking for {pattern}")


def dim_level_str_to_num(level_str):
    if level_str in LEVEL_NAME_TO_NUMBER:
        return LEVEL_NAME_TO_NUMBER[level_str]
    else:
        raise Exception(f"Unrecognized dimension level: {level_str}")


def extract_multi_dim_levels(filename):
    pattern = r"^(?P<Pitch>\w+)-(?P<Resonance>\w+)-(?P<Weight>\w+)\.wav$"
    match = re.search(pattern, filename)
    levels = {}
    if match:
        for dim in DIMENSIONS:
            dim_term = match.group(dim)
            dim_level_str = TERM_MAPPING[dim].get(dim_term)
            if dim_level_str is None:
                raise Exception(f"Unrecognized {dim} term: ${dim_term}")
            dim_level_num = dim_level_str_to_num(dim_level_str)
            levels[dim] = dim_level_num
        return levels
    else:
        raise Exception(f"Unrecognized combo name: {filename}")


def make_unique_path(path):
    if not os.path.exists(path):
        return path
    i = 1

    def get_new_path():
        return f"{path}_{i}"
    while os.path.exists(get_new_path()):
        i += 1
    return get_new_path()


def write_sample(output_dir, input_filepath, metadata):
    output_dirname = make_unique_path(os.path.join(
        output_dir, '_'.join(metadata.output_dir_components)))
    os.makedirs(output_dirname)
    shutil.copy(input_filepath, os.path.join(output_dirname, 'sample.wav'))
    with open(os.path.join(output_dirname, 'metadata.json'), 'w') as file:
        json.dump(metadata.metadata, file, indent=2)


def process_single_dimension_sample(output_dir, input_filename, input_filepath, dimension, metadata):
    dim_level_str = extract_dimension_level_string(input_filename, dimension)
    dim_level_num = dim_level_str_to_num(dim_level_str)
    metadata = metadata.clone_with(
        new_metadata={dimension: dim_level_num},
        new_output_dirname_components=[os.path.splitext(input_filename)[0]],
    )
    write_sample(output_dir, input_filepath, metadata)


def process_multi_dimension_sample(output_dir, input_filename, input_filepath, metadata):
    dim_levels = extract_multi_dim_levels(input_filename)
    metadata = metadata.clone_with(
        new_metadata=dim_levels,
        new_output_dirname_components=[os.path.splitext(input_filename)[0]],
    )
    write_sample(output_dir, input_filepath, metadata)


def process_single_dimension_subdir(output_dir, input_dir, dirname, metadata):
    dimension = dirname
    other_dimensions = [dim for dim in DIMENSIONS if dim is not dimension]
    for dim in other_dimensions:
        metadata = metadata.clone_with(new_metadata={dim: "Unlabeled"})

    for filename in os.listdir(input_dir):
        if filename.startswith('.'):
            continue

        filepath = os.path.join(input_dir, filename)

        if not os.path.isfile(filepath):
            process_single_dimension_subdir(
                output_dir, filepath, dirname, metadata)
        else:
            process_single_dimension_sample(
                output_dir, filename, filepath, dimension, metadata)


def process_multi_dimension_subdir(output_dir, input_dir, metadata):
    for filename in os.listdir(input_dir):
        if filename.startswith('.'):
            continue

        filepath = os.path.join(input_dir, filename)

        if not os.path.isfile(filepath):
            process_multi_dimension_subdir(output_dir, filepath, metadata)
        else:
            process_multi_dimension_sample(
                output_dir, filename, filepath, metadata)


def process_sample_subdir(output_dir, input_dir, dirname, metadata):
    if dirname in ('Pitch', 'Resonance', 'Weight'):
        process_single_dimension_subdir(
            output_dir, input_dir, dirname, metadata)
    elif dirname == 'Combos':
        process_multi_dimension_subdir(
            output_dir, input_dir, metadata)
    else:
        raise Exception(f"Unrecognized subdir name: {dirname}")


def process_sample_content(output_dir, input_dir, content_descriptor, metadata):
    metadata = metadata.clone_with(
        new_metadata={"content_descriptor": content_descriptor},
        new_output_dirname_components=[content_descriptor]
    )
    for dirname in os.listdir(input_dir):
        dirpath = os.path.join(input_dir, dirname)

        if dirname.startswith('.'):
            continue

        if os.path.isfile(dirpath):
            raise Exception(
                f"Unexpected file in second-level raw input files directory: {dirpath}")

        process_sample_subdir(output_dir, dirpath, dirname, metadata)


def process_files(raw_files_directory, output_directory):
    metadata = Metadata(metadata={
        "metadata_version": "0.0.1",
        "whose_voice_is_it": "Chloe",
        "who_evaluated_the_dimensions": "Chloe",
    }, output_dir_components=[])

    if not os.path.isdir(raw_files_directory):
        raise Exception(f"The directory {raw_files_directory} does not exist.")

    if os.path.exists(output_directory):
        shutil.rmtree(output_directory)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for dirname in os.listdir(raw_files_directory):
        dirpath = os.path.join(raw_files_directory, dirname)

        if dirname.startswith('.'):
            continue

        if os.path.isfile(dirpath):
            raise Exception(
                f"Unexpected file in top-level raw input files directory: {dirpath}")

        process_sample_content(output_directory, dirpath, dirname, metadata)


def main():
    parser = argparse.ArgumentParser(
        description="Read raw files, add tags, and write them to another directory.")
    parser.add_argument("--raw-files-directory",
                        help="Directory containing the raw text files.")
    parser.add_argument(
        "--output-directory", help="Directory where the output files will be stored.")

    args = parser.parse_args()
    process_files(args.raw_files_directory, args.output_directory)


if __name__ == '__main__':
    main()
