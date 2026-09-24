"""Independent checker for forced-cell fixed-codebook frontier certificates."""
from __future__ import annotations

import argparse
import itertools as it
import json
import resource
import signal
import time
from pathlib import Path


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def words(q: int, n: int) -> tuple[tuple[int, ...], ...]:
    return tuple(it.product(range(q), repeat=n))


def raw(word: tuple[int, ...], q: int) -> int:
    value = 0
    for symbol in word:
        value = (value << (1 if q == 2 else 2)) | (symbol if q == 2 else (0, 1, 3)[symbol])
    return value


def relation(spec: dict, encoder: tuple[int, ...], bound: int) -> tuple[tuple[int, ...], ...]:
    channel = words(spec["q"], spec["n"])
    pins = {row: message for message, row in enumerate(encoder)}
    rows: list[tuple[int, ...]] = []
    for received, y in enumerate(channel):
        sources = [
            message
            for message, code in enumerate(encoder)
            if sum(a != b for a, b in zip(channel[code], y)) <= spec["radius"]
        ]
        allowed = tuple(
            output
            for output in range(1 << spec["k"])
            if all((source ^ output).bit_count() <= bound for source in sources)
            and (received not in pins or output == pins[received])
        )
        rows.append(allowed)
    return tuple(rows)


def first_obstruction(spec: dict, encoder: tuple[int, ...], bound: int) -> dict | None:
    channel = words(spec["q"], spec["n"])
    pins = {row: message for message, row in enumerate(encoder)}
    for received, allowed in enumerate(relation(spec, encoder, bound)):
        if allowed:
            continue
        y = channel[received]
        sources = [
            message
            for message, code in enumerate(encoder)
            if sum(a != b for a, b in zip(channel[code], y)) <= spec["radius"]
        ]
        if received in pins:
            pinned = pins[received]
            bad = next(source for source in sources if (source ^ pinned).bit_count() > bound)
            return {"kind": "pin", "received_row": received, "source_messages": [bad], "pinned_message": pinned}
        core = list(sources)
        for source in list(sources):
            smaller = [candidate for candidate in core if candidate != source]
            if not any(
                all((candidate ^ output).bit_count() <= bound for candidate in smaller)
                for output in range(1 << spec["k"])
            ):
                core = smaller
        return {"kind": "empty_intersection", "received_row": received, "source_messages": core}
    return None


def cube_rows(width: int, count: int) -> tuple[tuple[str, tuple[int, ...]], ...]:
    result = []
    for digits in it.product((-1, 0, 1), repeat=width):
        matching = tuple(
            row
            for row in range(count)
            if all(
                digit == -1 or digit == ((row >> (width - 1 - j)) & 1)
                for j, digit in enumerate(digits)
            )
        )
        if matching:
            result.append(("".join("*" if d == -1 else str(d) for d in digits), matching))
    return tuple(result)


def eval_terms(domain: tuple[int, ...], width: int, outputs: int, terms: list[dict]) -> tuple[int, ...]:
    table = []
    for value in domain:
        bits = format(value, f"0{width}b")
        result = 0
        for term in terms:
            cube = term.get("cube")
            mask = term.get("outputs")
            need(isinstance(cube, str) and len(cube) == width and not (set(cube) - set("01*")), "bad term cube")
            need(isinstance(mask, int) and 0 < mask < (1 << outputs), "bad term mask")
            if all(c == "*" or c == bit for c, bit in zip(cube, bits)):
                result |= mask
        table.append(result)
    return tuple(table)


def expected_forced(legal: tuple[tuple[int, ...], ...], outputs: int) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    ones: set[tuple[int, int]] = set()
    zeros: set[tuple[int, int]] = set()
    for row, allowed in enumerate(legal):
        need(bool(allowed), "empty row in plane certificate")
        for output in range(outputs):
            bit = 1 << (outputs - 1 - output)
            flags = [bool(value & bit) for value in allowed]
            if all(flags):
                ones.add((row, output))
            if not any(flags):
                zeros.add((row, output))
    return ones, zeros


def check_plane(record: dict) -> dict:
    need(record.get("format") == "forced-cell-packing-v1", "unknown plane proof format")
    domain = tuple(record["domain"])
    width = int(record["width"])
    outputs = int(record["outputs"])
    legal = tuple(tuple(row) for row in record["legal_outputs"])
    need(len(domain) == len(legal), "plane row count mismatch")
    produced = eval_terms(domain, width, outputs, record["terms"])
    need(all(produced[row] in set(legal[row]) for row in range(len(domain))), "attaining circuit violates relation")
    need(len(record["terms"]) == record["minimum_products"], "product count mismatch")
    need(sum(term["outputs"].bit_count() for term in record["terms"]) == record["connections"], "connection count mismatch")

    forced_one, forced_zero = expected_forced(legal, outputs)
    listed_one = {tuple(cell) for cell in record["forced_one_cells"]}
    listed_zero = {tuple(cell) for cell in record["forced_zero_cells"]}
    need(listed_one == forced_one, "forced-one set mismatch")
    need(listed_zero == forced_zero, "forced-zero set mismatch")
    packing_list = [tuple(cell) for cell in record["packing"]]
    packing = set(packing_list)
    need(len(packing) == len(packing_list), "packing has duplicate cells")
    need(packing <= forced_one, "packing contains a non-forced-one cell")
    need(len(packing) == record["minimum_products"], "packing lower bound does not meet witness size")

    cubes = cube_rows(width, len(domain))
    checked_pairs = 0
    for left, right in it.combinations(sorted(packing), 2):
        checked_pairs += 1
        lr, lo = left
        rr, ro = right
        for cube, rows in cubes:
            if lr not in rows or rr not in rows:
                continue
            legal_left = not any((row, lo) in forced_zero for row in rows)
            legal_right = not any((row, ro) in forced_zero for row in rows)
            need(not (legal_left and legal_right), f"packing pair {left},{right} is co-coverable by {cube}")
    return {"cubes": len(cubes), "packing_pairs": checked_pairs, "products": record["minimum_products"]}


def check_certificate(spec: dict, cert: dict) -> dict:
    started = time.perf_counter()
    cpu = time.process_time()
    need(cert.get("format") == "fixed-codebook-frontier-v1", "unknown certificate format")
    case = cert["case"]
    for key in ("id", "q", "n", "k", "radius", "gate_cap", "connection_cap", "encoder"):
        need(case[key] == spec[key], f"case mismatch at {key}")
    channel = words(spec["q"], spec["n"])
    index = {"".join(map(str, word)): i for i, word in enumerate(channel)}
    encoder = tuple(index[word] for word in spec["encoder"])
    need(tuple(cert["encoder_rows"]) == encoder, "encoder row mapping mismatch")
    need(len(set(encoder)) == (1 << spec["k"]), "encoder is not injective")

    encoder_expected = tuple((raw(channel[row], spec["q"]),) for row in encoder)
    need(tuple(tuple(row) for row in cert["encoder_plane"]["legal_outputs"]) == encoder_expected, "encoder relation mismatch")
    stats = [check_plane(cert["encoder_plane"])]

    best: list[int | None] = [None] * (spec["k"] + 1)
    bound_records = cert["bounds"]
    need([item["error_bound"] for item in bound_records] == list(range(spec["k"] + 1)), "bound coverage mismatch")
    for item in bound_records:
        bound = item["error_bound"]
        rows = relation(spec, encoder, bound)
        obstruction = first_obstruction(spec, encoder, bound)
        if obstruction is not None:
            need(item == {"error_bound": bound, "semantic_obstruction": obstruction}, "semantic obstruction mismatch")
            continue
        need("decoder_plane" in item, "feasible bound lacks plane proof")
        plane = item["decoder_plane"]
        need(tuple(tuple(row) for row in plane["legal_outputs"]) == rows, "decoder row relation mismatch")
        stats.append(check_plane(plane))
        gates = cert["encoder_plane"]["minimum_products"] + plane["minimum_products"] + spec["n"] + spec["k"]
        connections = cert["encoder_plane"]["connections"] + plane["connections"]
        need(gates == item["gates"] and connections == item["connections"], "objective mismatch")
        need(gates <= spec["gate_cap"] and connections <= spec["connection_cap"], "cap violation")
        best[bound] = gates
    need(best == cert["best_cost_by_error_bound"], "best-cost profile mismatch")

    frontier = []
    previous = None
    for bound, gates in enumerate(best):
        if gates is not None and (previous is None or gates < previous):
            frontier.append({"error_bound": bound, "gates": gates, "connections": bound_records[bound]["connections"]})
            previous = gates
    need(frontier == cert["frontier"], "frontier mismatch")
    free_rows = len(channel) - (1 << spec["k"])
    completions = (1 << spec["k"]) ** free_rows
    need(cert["decoder_completion_count"] == completions, "decoder completion count mismatch")
    need(cert["decoder_completion_count_power_of_two"] == spec["k"] * free_rows, "completion exponent mismatch")
    return {
        "accepted": True,
        "case": spec["id"],
        "planes_checked": len(stats),
        "cubes_checked": sum(item["cubes"] for item in stats),
        "packing_pairs_checked": sum(item["packing_pairs"] for item in stats),
        "frontier": [[point["error_bound"], point["gates"]] for point in frontier],
        "checker_cpu_seconds": time.process_time() - cpu,
        "checker_wall_seconds": time.perf_counter() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--inputs", type=Path, default=Path("inputs/fixed-codebooks.json"))
    parser.add_argument("--certificate-dir", type=Path, default=Path("results/fixed-codebook"))
    args = parser.parse_args()
    signal.alarm(600)
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
    specs = json.loads(args.inputs.read_text())
    spec = next((item for item in specs if item["id"] == args.case), None)
    if spec is None:
        raise ValueError("unknown fixed-codebook case")
    cert = json.loads((args.certificate_dir / f"{args.case}.json").read_text())
    result = check_certificate(spec, cert)
    (args.certificate_dir / f"{args.case}-check.json").write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
