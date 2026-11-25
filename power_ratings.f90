program power_ratings
    implicit none

    integer, parameter :: n = 32
    integer, parameter :: n_sims = 100000

    character(len=3) :: abbr(n), tmp_abbr
    integer :: div_id(n), gp(n), w(n), l(n), otl(n), pts(n), gf(n), ga(n)
    integer :: tmp_i
    real(8) :: pyth_pct(n), colley_r(n), blend_pct(n)
    real(8) :: proj_pts(n), diff_pg(n), playoff_pct(n), cup_pct(n)
    real(8) :: tmp_r, gf_exp, ga_exp

    ! Colley Matrix variables
    integer :: n_comp, hs, as_, c_played(n), c_wins(n), c_losses(n)
    real(8) :: C_mat(n, n), b_vec(n)

    ! Schedule & simulation arrays
    integer :: n_rem, sim, g, h, a, d, k, idx1, idx2
    integer, allocatable :: home_id(:), away_id(:)
    real(8), allocatable :: win_prob(:)
    real(8) :: ph, pa, log5, r1, r2
    integer :: sim_pts(n), sim_w(n), score(n), playoff_hits(n), cup_hits(n)
    integer :: div_teams(4, 8), div_count(4), div_ord(4, 8), ord(8)
    integer :: east_pool(10), west_pool(10)
    integer :: e_top1, e_top2, e_bot1, e_bot2, e_r2_a, e_r2_b, east_champ
    integer :: w_top1, w_top2, w_bot1, w_bot2, w_r2_a, w_r2_b, west_champ
    integer :: cup_winner

    ! 1. Read team stats & compute Pythagorean Win %
    open(unit=10, file="fortran_in.txt", status="old", action="read")
    do h = 1, n
        read(10, *) abbr(h), div_id(h), gp(h), w(h), l(h), otl(h), pts(h), gf(h), ga(h)

        gf_exp = dble(gf(h)) ** 2.15d0
        ga_exp = dble(ga(h)) ** 2.15d0
        pyth_pct(h) = gf_exp / (gf_exp + ga_exp)
        diff_pg(h)  = dble(gf(h) - ga(h)) / dble(gp(h))
    end do
    close(10)

    ! 2. Build and solve the 32x32 Colley Matrix system (C * r = b)
    C_mat    = 0.0d0
    b_vec    = 0.0d0
    c_played = 0
    c_wins   = 0
    c_losses = 0

    open(unit=12, file="fortran_completed.txt", status="old", action="read")
    read(12, *) n_comp
    do g = 1, n_comp
        read(12, *) h, a, hs, as_
        c_played(h) = c_played(h) + 1
        c_played(a) = c_played(a) + 1
        C_mat(h, a) = C_mat(h, a) - 1.0d0
        C_mat(a, h) = C_mat(a, h) - 1.0d0

        if (hs > as_) then
            c_wins(h)   = c_wins(h) + 1
            c_losses(a) = c_losses(a) + 1
        else
            c_wins(a)   = c_wins(a) + 1
            c_losses(h) = c_losses(h) + 1
        end if
    end do
    close(12)

    do h = 1, n
        C_mat(h, h) = 2.0d0 + dble(c_played(h))
        b_vec(h)    = 1.0d0 + 0.5d0 * dble(c_wins(h) - c_losses(h))
    end do

    call solve_colley(n, C_mat, b_vec, colley_r)

    ! Blend 50% Pythagorean (margin-of-victory) + 50% Colley (strength-of-schedule)
    do h = 1, n
        blend_pct(h) = 0.50d0 * pyth_pct(h) + 0.50d0 * colley_r(h)
        proj_pts(h)  = blend_pct(h) * 164.0d0
    end do

    ! Group team indices by division (1=A, 2=M, 3=C, 4=P)
    div_count = 0
    do h = 1, n
        d = div_id(h)
        div_count(d) = div_count(d) + 1
        div_teams(d, div_count(d)) = h
    end do

    ! 3. Read remaining games & precompute Log5 home win probabilities using blended strength
    open(unit=11, file="fortran_sched.txt", status="old", action="read")
    read(11, *) n_rem
    allocate(home_id(n_rem), away_id(n_rem), win_prob(n_rem))
    do g = 1, n_rem
        read(11, *) home_id(g), away_id(g)
        ph = blend_pct(home_id(g))
        pa = blend_pct(away_id(g))
        log5 = (ph * (1.0d0 - pa)) / (ph * (1.0d0 - pa) + (1.0d0 - ph) * pa)
        win_prob(g) = min(0.92d0, max(0.08d0, log5 + 0.035d0))
    end do
    close(11)

    ! 4. Run 100,000 full-season + 4-round playoff simulations
    call random_seed()
    playoff_hits = 0
    cup_hits     = 0

    do sim = 1, n_sims
        sim_pts = pts
        sim_w   = w

        do g = 1, n_rem
            h = home_id(g)
            a = away_id(g)
            call random_number(r1)
            call random_number(r2)
            if (r1 < win_prob(g)) then
                sim_pts(h) = sim_pts(h) + 2
                sim_w(h)   = sim_w(h) + 1
                if (r2 < 0.23d0) sim_pts(a) = sim_pts(a) + 1
            else
                sim_pts(a) = sim_pts(a) + 2
                sim_w(a)   = sim_w(a) + 1
                if (r2 < 0.23d0) sim_pts(h) = sim_pts(h) + 1
            end if
        end do

        do h = 1, n
            score(h) = sim_pts(h) * 100 + sim_w(h)
        end do

        do d = 1, 4
            ord = div_teams(d, 1:8)
            do idx1 = 1, 7
                do idx2 = idx1 + 1, 8
                    if (score(ord(idx2)) > score(ord(idx1))) then
                        tmp_i     = ord(idx1)
                        ord(idx1) = ord(idx2)
                        ord(idx2) = tmp_i
                    end if
                end do
            end do

            div_ord(d, 1:8) = ord(1:8)
            do k = 1, 3
                playoff_hits(ord(k)) = playoff_hits(ord(k)) + 1
            end do

            if (d == 1) east_pool(1:5)  = ord(4:8)
            if (d == 2) east_pool(6:10) = ord(4:8)
            if (d == 3) west_pool(1:5)  = ord(4:8)
            if (d == 4) west_pool(6:10) = ord(4:8)
        end do

        do idx1 = 1, 2
            do idx2 = idx1 + 1, 10
                if (score(east_pool(idx2)) > score(east_pool(idx1))) then
                    tmp_i           = east_pool(idx1)
                    east_pool(idx1) = east_pool(idx2)
                    east_pool(idx2) = tmp_i
                end if
            end do
            playoff_hits(east_pool(idx1)) = playoff_hits(east_pool(idx1)) + 1
        end do

        do idx1 = 1, 2
            do idx2 = idx1 + 1, 10
                if (score(west_pool(idx2)) > score(west_pool(idx1))) then
                    tmp_i           = west_pool(idx1)
                    west_pool(idx1) = west_pool(idx2)
                    west_pool(idx2) = tmp_i
                end if
            end do
            playoff_hits(west_pool(idx1)) = playoff_hits(west_pool(idx1)) + 1
        end do

        ! Eastern Conference Bracket
        if (score(div_ord(1, 1)) >= score(div_ord(2, 1))) then
            e_top1 = sim_series(div_ord(1, 1), east_pool(2), blend_pct, score)
            e_top2 = sim_series(div_ord(1, 2), div_ord(1, 3), blend_pct, score)
            e_bot1 = sim_series(div_ord(2, 1), east_pool(1), blend_pct, score)
            e_bot2 = sim_series(div_ord(2, 2), div_ord(2, 3), blend_pct, score)
        else
            e_top1 = sim_series(div_ord(2, 1), east_pool(2), blend_pct, score)
            e_top2 = sim_series(div_ord(2, 2), div_ord(2, 3), blend_pct, score)
            e_bot1 = sim_series(div_ord(1, 1), east_pool(1), blend_pct, score)
            e_bot2 = sim_series(div_ord(1, 2), div_ord(1, 3), blend_pct, score)
        end if
        e_r2_a     = sim_series(e_top1, e_top2, blend_pct, score)
        e_r2_b     = sim_series(e_bot1, e_bot2, blend_pct, score)
        east_champ = sim_series(e_r2_a, e_r2_b, blend_pct, score)

        ! Western Conference Bracket
        if (score(div_ord(3, 1)) >= score(div_ord(4, 1))) then
            w_top1 = sim_series(div_ord(3, 1), west_pool(2), blend_pct, score)
            w_top2 = sim_series(div_ord(3, 2), div_ord(3, 3), blend_pct, score)
            w_bot1 = sim_series(div_ord(4, 1), west_pool(1), blend_pct, score)
            w_bot2 = sim_series(div_ord(4, 2), div_ord(4, 3), blend_pct, score)
        else
            w_top1 = sim_series(div_ord(4, 1), west_pool(2), blend_pct, score)
            w_top2 = sim_series(div_ord(4, 2), div_ord(4, 3), blend_pct, score)
            w_bot1 = sim_series(div_ord(3, 1), west_pool(1), blend_pct, score)
            w_bot2 = sim_series(div_ord(3, 2), div_ord(3, 3), blend_pct, score)
        end if
        w_r2_a     = sim_series(w_top1, w_top2, blend_pct, score)
        w_r2_b     = sim_series(w_bot1, w_bot2, blend_pct, score)
        west_champ = sim_series(w_r2_a, w_r2_b, blend_pct, score)

        ! Stanley Cup Final
        cup_winner = sim_series(east_champ, west_champ, blend_pct, score)
        cup_hits(cup_winner) = cup_hits(cup_winner) + 1
    end do

    do h = 1, n
        playoff_pct(h) = (dble(playoff_hits(h)) / dble(n_sims)) * 100.0d0
        cup_pct(h)     = (dble(cup_hits(h))     / dble(n_sims)) * 100.0d0
    end do

    ! 5. Sort teams by blended Power Rating (Pythagorean + Colley)
    do idx1 = 1, n - 1
        do idx2 = idx1 + 1, n
            if (blend_pct(idx2) > blend_pct(idx1)) then
                tmp_abbr = abbr(idx1);        abbr(idx1)        = abbr(idx2);        abbr(idx2)        = tmp_abbr
                tmp_i    = pts(idx1);         pts(idx1)         = pts(idx2);         pts(idx2)         = tmp_i
                tmp_r    = pyth_pct(idx1);    pyth_pct(idx1)    = pyth_pct(idx2);    pyth_pct(idx2)    = tmp_r
                tmp_r    = colley_r(idx1);    colley_r(idx1)    = colley_r(idx2);    colley_r(idx2)    = tmp_r
                tmp_r    = blend_pct(idx1);   blend_pct(idx1)   = blend_pct(idx2);   blend_pct(idx2)   = tmp_r
                tmp_r    = proj_pts(idx1);    proj_pts(idx1)    = proj_pts(idx2);    proj_pts(idx2)    = tmp_r
                tmp_r    = diff_pg(idx1);     diff_pg(idx1)     = diff_pg(idx2);     diff_pg(idx2)     = tmp_r
                tmp_r    = playoff_pct(idx1); playoff_pct(idx1) = playoff_pct(idx2); playoff_pct(idx2) = tmp_r
                tmp_r    = cup_pct(idx1);     cup_pct(idx1)     = cup_pct(idx2);     cup_pct(idx2)     = tmp_r
            end if
        end do
    end do

    ! 6. Save to file for HTML builder (now includes Colley Rating in column 4)
    open(unit=20, file="fortran_ranked.txt", status="replace", action="write")
    do h = 1, n
        write(20, '(I2, 1X, A3, 1X, F6.4, 1X, F6.4, 1X, F6.1, 1X, F6.2, 1X, F6.1, 1X, F5.1)') &
            h, abbr(h), pyth_pct(h), colley_r(h), proj_pts(h), diff_pg(h), playoff_pct(h), cup_pct(h)
    end do
    close(20)

    print '(A)', "Solved Colley Matrix + 100,000 Stanley Cup simulations!"

contains

    subroutine solve_colley(dim, A_in, b_in, x_out)
        integer, intent(in) :: dim
        real(8), intent(in) :: A_in(dim, dim), b_in(dim)
        real(8), intent(out) :: x_out(dim)
        real(8) :: aug(dim, dim + 1), factor, max_val, tmp_row(dim + 1)
        integer :: i, j, k, max_row

        aug(:, 1:dim)   = A_in
        aug(:, dim + 1) = b_in

        ! Forward elimination with partial pivoting
        do k = 1, dim - 1
            max_val = abs(aug(k, k))
            max_row = k
            do i = k + 1, dim
                if (abs(aug(i, k)) > max_val) then
                    max_val = abs(aug(i, k))
                    max_row = i
                end if
            end do
            if (max_row /= k) then
                tmp_row        = aug(k, :)
                aug(k, :)      = aug(max_row, :)
                aug(max_row, :) = tmp_row
            end if

            do i = k + 1, dim
                factor = aug(i, k) / aug(k, k)
                aug(i, k:dim+1) = aug(i, k:dim+1) - factor * aug(k, k:dim+1)
            end do
        end do

        ! Back substitution
        do i = dim, 1, -1
            x_out(i) = aug(i, dim + 1)
            do j = i + 1, dim
                x_out(i) = x_out(i) - aug(i, j) * x_out(j)
            end do
            x_out(i) = x_out(i) / aug(i, i)
        end do
    end subroutine solve_colley

    integer function sim_series(t1, t2, strength, reg_score)
        integer, intent(in) :: t1, t2
        real(8), intent(in) :: strength(32)
        integer, intent(in) :: reg_score(32)
        integer :: hi, lo, hi_wins, lo_wins, game_num
        real(8) :: p_hi, p_lo, base_p, game_p, rnd

        if (reg_score(t1) >= reg_score(t2)) then
            hi = t1
            lo = t2
        else
            hi = t2
            lo = t1
        end if

        p_hi = strength(hi)
        p_lo = strength(lo)
        base_p = (p_hi * (1.0d0 - p_lo)) / (p_hi * (1.0d0 - p_lo) + (1.0d0 - p_hi) * p_lo)

        hi_wins = 0
        lo_wins = 0
        game_num = 0

        do while (hi_wins < 4 .and. lo_wins < 4)
            game_num = game_num + 1
            if (game_num == 1 .or. game_num == 2 .or. game_num == 5 .or. game_num == 7) then
                game_p = min(0.92d0, max(0.08d0, base_p + 0.035d0))
            else
                game_p = min(0.92d0, max(0.08d0, base_p - 0.035d0))
            end if

            call random_number(rnd)
            if (rnd < game_p) then
                hi_wins = hi_wins + 1
            else
                lo_wins = lo_wins + 1
            end if
        end do

        if (hi_wins == 4) then
            sim_series = hi
        else
            sim_series = lo
        end if
    end function sim_series

end program power_ratings