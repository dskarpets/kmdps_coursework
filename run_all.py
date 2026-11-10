from experiments import baseline, bias_study, replication_study, transient_study
from identification import identify
from modifications import modifications
from main import print_report, run
from verify import print_trace_examples, verification


def main():
    print("Контрольний запуск (T_mod = 100000 с):")
    print_report(run(t_mod=100000.0)[0])
    print("\nПротокол подій:")
    print_trace_examples()
    print()
    verification()
    print()
    transient_study()
    print()
    bias_study()
    print()
    replication_study()
    print()
    baseline()
    print()
    identify()
    print()
    modifications()


if __name__ == "__main__":
    main()
