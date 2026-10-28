from experiments import baseline, replication_study, transient_study
from identification import identify
from main import print_report, run
from verify import print_trace_examples, verification


def main():
    print("Контрольний запуск (seed = 1, T_mod = 100000 с):")
    print_report(run(t_mod=100000.0, seed=1)[2])

    print("\nПротокол подій:")
    print_trace_examples()

    print()
    verification()

    print()
    transient_study()

    print()
    replication_study()

    print()
    baseline()

    print()
    identify()


if __name__ == "__main__":
    main()
