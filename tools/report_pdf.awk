BEGIN {
    FS = ","
}

FNR == 1 {
    next
}

FILENAME ~ /results[.]csv$/ {
    chain_count++
    chain_alpha[chain_count] = $1
    chain_items[chain_count] = $2
    chain_hit[chain_count] = $3
    chain_hit_theory[chain_count] = $4
    chain_miss[chain_count] = $5
    chain_miss_theory[chain_count] = $6
    next
}

FILENAME ~ /comparison_experiment[.]csv$/ {
    compare_count++
    compare_alpha[compare_count] = $1
    compare_items[compare_count] = $2
    compare_chain_hit[compare_count] = $3
    compare_chain_miss[compare_count] = $5
    compare_linear_hit[compare_count] = $7
    compare_linear_miss[compare_count] = $9
}

function text_line(font, size, x, y, text) {
    return "BT /" font " " size " Tf 1 0 0 1 " x " " y " Tm (" text ") Tj ET\n"
}

function add_object(number, contents) {
    offsets[number] = length(document)
    document = document number " 0 obj\n" contents "\nendobj\n"
}

END {
    if (chain_count != 16 || compare_count != 9) {
        print "Expected 16 chaining rows and 9 comparison rows" > "/dev/stderr"
        exit 1
    }

    page_one = text_line("F1", 18, 48, 748, "Hash table comparison report")
    page_one = page_one text_line("F1", 11, 48, 724, "Separate chaining at load factors alpha 0.25 through 4.00")
    page_one = page_one text_line("F1", 10, 48, 698, "Capacity 4093. Random URLs; 4093 absent-key queries per load.")
    page_one = page_one text_line("F2", 9, 48, 672, "alpha    items     success measured/theory       failure measured/theory")
    for (i = 1; i <= chain_count; i++) {
        row = sprintf("%5.2f %7d      %5.3f / %5.3f              %5.3f / %5.3f", \
            chain_alpha[i], chain_items[i], chain_hit[i], chain_hit_theory[i], \
            chain_miss[i], chain_miss_theory[i])
        page_one = page_one text_line("F2", 8, 48, 652 - 14 * (i - 1), row)
    }
    page_one = page_one text_line("F1", 10, 48, 412, "Theory: successful lookup is 1 + alpha/2; unsuccessful lookup is alpha.")
    page_one = page_one text_line("F1", 10, 48, 392, "Measured costs stay close to theory across the full range.")
    page_one = page_one text_line("F1", 10, 48, 374, "At alpha 4, the measured costs are 3.001 successful and 3.983 unsuccessful.")
    page_one = page_one text_line("F1", 10, 48, 356, "Small deviations reflect finite samples and hash bucket distribution.")
    page_one = page_one text_line("F1", 9, 48, 320, "The complete dataset and plot are in experiments/results.csv and .svg.")
    page_one = page_one text_line("F1", 9, 48, 300, "The comparison experiment uses the same keys and capacity for both implementations.")

    page_two = text_line("F1", 18, 48, 748, "Chaining versus linear probing")
    page_two = page_two text_line("F1", 11, 48, 724, "Load factors alpha 0.1 through 0.9; both tables use the same keys.")
    page_two = page_two text_line("F2", 8, 48, 694, "alpha   items     chain hit   chain miss    linear hit   linear miss")
    for (i = 1; i <= compare_count; i++) {
        row = sprintf("%4.1f %7d      %6.3f      %6.3f       %6.3f      %7.3f", \
            compare_alpha[i], compare_items[i], compare_chain_hit[i], \
            compare_chain_miss[i], compare_linear_hit[i], compare_linear_miss[i])
        page_two = page_two text_line("F2", 8, 48, 674 - 16 * (i - 1), row)
    }
    page_two = page_two text_line("F1", 9, 48, 518, "Chaining theory: hit 1 + alpha/2; miss alpha.")
    page_two = page_two text_line("F1", 9, 48, 500, "Linear theory: hit is 0.5 times one plus one divided by one minus alpha.")
    page_two = page_two text_line("F1", 9, 48, 482, "Miss is 0.5 times one plus one divided by the square of one minus alpha.")
    page_two = page_two text_line("F1", 9, 48, 450, "At alpha 0.9, linear probing averages 5.496 hits and 48.670 misses.")
    page_two = page_two text_line("F1", 9, 48, 432, "The theoretical values are 5.500 and 50.500; the sharp rise is primary clustering.")
    page_two = page_two text_line("F1", 9, 48, 414, "Chaining remains near its estimates: 1.455 hits and 0.913 misses at alpha 0.9.")
    page_two = page_two text_line("F1", 9, 48, 382, "Linear probing is competitive at low load but degrades rapidly near a full table.")
    page_two = page_two text_line("F1", 9, 48, 364, "The comparison graph and full measurements are in experiments/comparison_experiment.")
    page_two = page_two text_line("F1", 9, 48, 328, "Method: fixed capacity 4096, seed 2026, fixed key sequences, standard-library code.")
    page_two = page_two text_line("F1", 9, 48, 310, "Successful costs average every stored key; failed costs average 4096 absent keys.")

    document = "%PDF-1.4\n"
    add_object(1, "<< /Type /Catalog /Pages 2 0 R >>")
    add_object(2, "<< /Type /Pages /Kids [3 0 R 6 0 R] /Count 2 >>")
    add_object(3, "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R /F2 8 0 R >> >> /Contents 4 0 R >>")
    add_object(4, "<< /Length " length(page_one) " >>\nstream\n" page_one "endstream")
    add_object(5, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    add_object(6, "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R /F2 8 0 R >> >> /Contents 7 0 R >>")
    add_object(7, "<< /Length " length(page_two) " >>\nstream\n" page_two "endstream")
    add_object(8, "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    xref_offset = length(document)
    document = document "xref\n0 9\n0000000000 65535 f \n"
    for (i = 1; i <= 8; i++) {
        document = document sprintf("%010d 00000 n \n", offsets[i])
    }
    document = document "trailer\n<< /Size 9 /Root 1 0 R >>\nstartxref\n" xref_offset "\n%%EOF\n"
    printf "%s", document > "REPORT.pdf"
    close("REPORT.pdf")
    print "Wrote REPORT.pdf with two pages"
}
