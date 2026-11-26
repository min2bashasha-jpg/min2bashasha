import math  # 삼각함수와 라디안 변환 등 순수 수학 연산을 위해 내장 math 모듈을 불러옵니다.
import turtle  # 외부 설치 없이 2D 벡터 그래픽을 그리기 위해 내장 turtle 모듈을 불러옵니다.

SCALE = 38.0  # 수학적 모델 좌표(-9~9)를 픽셀 화면 크기로 확대할 배율 상수를 정의합니다.

def sample_cubic_bezier(p0, p1, p2, p3, steps=20):  # 4개의 제어점으로 3차 베지어 곡선 위의 점들을 추출하는 함수입니다.
    pts = []  # 계산된 곡선 좌표를 순서대로 담을 빈 리스트를 초기화합니다.
    for i in range(1, steps + 1):  # 시작점을 제외하고 끝점까지 지정된 분할 횟수만큼 반복합니다.
        u = i / steps  # 0에서 1 사이를 균등하게 나눈 곡선 매개변수 u를 계산합니다.
        inv = 1.0 - u  # 베지어 공식의 (1 - u) 항을 미리 계산해 연산 중복을 줄입니다.
        x = (inv ** 3) * p0[0] + 3 * (inv ** 2) * u * p1[0] + 3 * inv * (u ** 2) * p2[0] + (u ** 3) * p3[0]  # 3차 베지어 다항식으로 x 좌표를 구합니다.
        y = (inv ** 3) * p0[1] + 3 * (inv ** 2) * u * p1[1] + 3 * inv * (u ** 2) * p2[1] + (u ** 3) * p3[1]  # 3차 베지어 다항식으로 y 좌표를 구합니다.
        pts.append((x, y))  # 산출된 (x, y) 좌표 튜플을 리스트에 추가합니다.
    return pts  # 샘플링이 완료된 곡선 정점 리스트를 반환합니다.

def build_bezier_points(start, segments, steps=20):  # 여러 베지어 곡선 구간을 이어 붙여 하나의 정점 열로 만드는 함수입니다.
    pts = [start]  # 첫 번째 시작 좌표를 정점 리스트의 초깃값으로 설정합니다.
    curr = start  # 현재 곡선 구간의 출발점을 시작 좌표로 초기화합니다.
    for c1, c2, end in segments:  # 각 구간의 제어점 2개와 도착점 1개를 순회합니다.
        pts.extend(sample_cubic_bezier(curr, c1, c2, end, steps))  # 현재 구간의 곡선 정점들을 리스트 뒤에 이어 붙입니다.
        curr = end  # 다음 구간의 출발점을 현재 구간의 도착점으로 갱신합니다.
    return pts  # 전체 윤곽을 구성하는 정점 리스트를 반환합니다.

def mirror_segments_x(segments):  # 베지어 구간 목록의 x 좌표 부호를 반전시켜 좌우 대칭 구간을 만드는 함수입니다.
    return [((-c1[0], c1[1]), (-c2[0], c2[1]), (-end[0], end[1])) for c1, c2, end in segments]  # 리스트 컴프리헨션으로 모든 x 값을 음수 변환해 반환합니다.

def point_in_polygon(px, py, poly):  # 광선 투사법(Ray-Casting)으로 특정 점이 다각형 내부에 있는지 판별하는 함수입니다.
    inside = False  # 점의 내부 포함 여부를 거짓으로 초기화합니다.
    n = len(poly)  # 다각형을 이루는 전체 정점의 개수를 구합니다.
    j = n - 1  # 직전 정점 인덱스를 마지막 정점으로 설정해 닫힌 변을 검사합니다.
    for i in range(n):  # 다각형의 모든 변을 순회하며 수평 반직선과의 교차 여부를 확인합니다.
        xi, yi = poly[i]  # 현재 정점의 x, y 좌표를 꺼냅니다.
        xj, yj = poly[j]  # 직전 정점의 x, y 좌표를 꺼냅니다.
        if (yi > py) != (yj > py):  # 변의 양 끝점이 검사할 점의 y 좌표를 사이에 두고 걸치는지 확인합니다.
            intersect_x = (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi  # 수평선 y=py와 현재 변이 만나는 교점의 x 좌표를 계산합니다.
            if px < intersect_x:  # 교점이 검사할 점보다 오른쪽에 있다면 반직선과 교차한 것으로 판단합니다.
                inside = not inside  # 교차할 때마다 내부·외부 상태를 반전시킵니다(홀수 번 교차 시 내부).
        j = i  # 다음 변 검사를 위해 현재 인덱스를 직전 인덱스로 갱신합니다.
    return inside  # 최종 판별된 다각형 내부 포함 여부(True/False)를 반환합니다.

def ellipse_points(cx, cy, rx, ry, angle_deg=0.0, steps=48):  # 회전된 타원의 외곽 정점 리스트를 생성하는 함수입니다.
    rad = math.radians(angle_deg)  # 도 단위의 회전 각도를 라디안으로 변환합니다.
    cos_a = math.cos(rad)  # 회전 행렬에 사용할 코사인 값을 미리 계산합니다.
    sin_a = math.sin(rad)  # 회전 행렬에 사용할 사인 값을 미리 계산합니다.
    pts = []  # 타원 외곽 정점을 저장할 빈 리스트를 생성합니다.
    for i in range(steps):  # 지정된 분할 수만큼 360도를 순회합니다.
        theta = 2.0 * math.pi * i / steps  # 현재 단계의 중심각 세타를 라디안으로 계산합니다.
        lx = rx * math.cos(theta)  # 회전 전 로컬 좌표계에서의 타원 x 좌표를 구합니다.
        ly = ry * math.sin(theta)  # 회전 전 로컬 좌표계에서의 타원 y 좌표를 구합니다.
        gx = cx + lx * cos_a - ly * sin_a  # 2D 회전 변환과 중심 이동을 적용한 최종 x 좌표를 계산합니다.
        gy = cy + lx * sin_a + ly * cos_a  # 2D 회전 변환과 중심 이동을 적용한 최종 y 좌표를 계산합니다.
        pts.append((gx, gy))  # 변환된 정점 좌표를 리스트에 추가합니다.
    return pts  # 완성된 타원 정점 리스트를 반환합니다.

def get_mouth_contour(cx, cy, rx, ry_up, ry_down, num_pts=120):  # 상하 반지름이 다른 비대칭 아치형 입 윤곽 좌표를 구하는 함수입니다.
    pts = []  # 입 윤곽 좌표를 저장할 리스트를 초기화합니다.
    for i in range(num_pts):  # 360도를 균등하게 분할한 각도를 순회합니다.
        angle = 2.0 * math.pi * i / num_pts  # 현재 정점의 라디안 각도를 계산합니다.
        sin_v = math.sin(angle)  # 각도의 사인 값을 미리 계산해 상·하 절반 판별에 재사용합니다.
        ry = ry_up if sin_v >= 0 else ry_down  # 윗입술 영역과 아랫입술 영역에 서로 다른 세로 반지름을 적용합니다.
        pts.append((cx + rx * math.cos(angle), cy + ry * sin_v))  # 극좌표 공식을 직교좌표로 변환해 리스트에 추가합니다.
    return pts  # 완성된 입 윤곽 좌표 리스트를 반환합니다.

def draw_polygon(t, pts, fill_color=None, line_color=None, width=2.0, closed=True):  # 정점 리스트를 받아 거북이 펜으로 면 채우기 및 선 그리기를 수행하는 함수입니다.
    if not pts:  # 전달된 정점 리스트가 비어 있다면 그리기 오류를 막기 위해 즉시 종료합니다.
        return  # 빈 입력에 대해 함수를 반환합니다.
    t.penup()  # 이동 중 불필요한 선이 그려지지 않도록 펜을 듭니다.
    t.goto(pts[0][0] * SCALE, pts[0][1] * SCALE)  # 첫 번째 정점을 픽셀 좌표로 환산해 이동합니다.
    if fill_color is not None:  # 면 채우기 색상이 지정된 경우 채우기 블록을 실행합니다.
        t.fillcolor(fill_color)  # 내부를 채울 색상을 설정합니다.
        t.pencolor(line_color if line_color is not None else fill_color)  # 외곽선이 없으면 채움색과 같은 펜 색을 써서 이음새를 감춥니다.
        t.pensize(width if line_color is not None else 1)  # 외곽선 유무에 따라 선 굵기를 설정합니다.
        t.pendown()  # 선 그리기 및 채우기 영역 기록을 시작하기 위해 펜을 내립니다.
        t.begin_fill()  # 다각형 내부 색상 채우기를 시작합니다.
        for x, y in pts[1:]:  # 두 번째 정점부터 마지막 정점까지 순회하며 선을 잇습니다.
            t.goto(x * SCALE, y * SCALE)  # 각 정점을 스케일 변환해 거북이를 이동합니다.
        if closed:  # 닫힌 도형 옵션이 켜져 있다면 시작점으로 돌아가 경로를 닫습니다.
            t.goto(pts[0][0] * SCALE, pts[0][1] * SCALE)  # 출발 좌표로 복귀해 도형을 마감합니다.
        t.end_fill()  # 기록된 다각형 내부를 설정된 색상으로 채워 마무리합니다.
        t.penup()  # 다음 도형 이동을 위해 펜을 듭니다.
    elif line_color is not None:  # 면 채우기 없이 외곽선만 그려야 하는 경우를 처리합니다.
        t.pencolor(line_color)  # 외곽선 색상을 설정합니다.
        t.pensize(width)  # 외곽선 굵기를 설정합니다.
        t.pendown()  # 선을 그리기 위해 펜을 내립니다.
        for x, y in pts[1:]:  # 두 번째 정점부터 끝까지 순회하며 윤곽선을 그립니다.
            t.goto(x * SCALE, y * SCALE)  # 각 정점의 화면 좌표로 선을 긋습니다.
        if closed:  # 닫힌 외곽선이라면 시작점으로 돌아와 선을 닫습니다.
            t.goto(pts[0][0] * SCALE, pts[0][1] * SCALE)  # 출발 좌표로 복귀해 외곽선을 완성합니다.
        t.penup()  # 그리기가 끝났으므로 펜을 듭니다.

def draw_tooth(t, cx, cy, rx, ry_up, ry_down, angle_deg, half_width_deg, tip_scale):  # 지정된 극좌표 각도에 상어 이빨 하나를 그리는 함수입니다.
    a_mid = math.radians(angle_deg)  # 이빨 중앙 각도를 라디안으로 변환합니다.
    a_left = math.radians(angle_deg - half_width_deg)  # 이빨 왼쪽 밑변의 라디안 각도를 계산합니다.
    a_right = math.radians(angle_deg + half_width_deg)  # 이빨 오른쪽 밑변의 라디안 각도를 계산합니다.
    base_scale = 0.90  # 이빨 뿌리가 잇몸 안쪽에 자연스럽게 위치하도록 반지름 비율을 지정합니다.
    ry_l = ry_up if math.sin(a_left) >= 0 else ry_down  # 왼쪽 밑변 위치에 해당하는 상·하 세로 반지름을 선택합니다.
    ry_r = ry_up if math.sin(a_right) >= 0 else ry_down  # 오른쪽 밑변 위치에 해당하는 상·하 세로 반지름을 선택합니다.
    ry_m = ry_up if math.sin(a_mid) >= 0 else ry_down  # 이빨 중앙 위치에 해당하는 상·하 세로 반지름을 선택합니다.
    p_left = (cx + rx * base_scale * math.cos(a_left), cy + ry_l * base_scale * math.sin(a_left))  # 이빨 왼쪽 밑변 좌표를 계산합니다.
    p_right = (cx + rx * base_scale * math.cos(a_right), cy + ry_r * base_scale * math.sin(a_right))  # 이빨 오른쪽 밑변 좌표를 계산합니다.
    p_tip = (cx + rx * tip_scale * math.cos(a_mid), cy + ry_m * tip_scale * math.sin(a_mid))  # 입 중앙을 향하는 뾰족한 끝점 좌표를 계산합니다.
    p_base = (cx + rx * (base_scale + 0.04) * math.cos(a_mid), cy + ry_m * (base_scale + 0.04) * math.sin(a_mid))  # 뿌리 부분을 살짝 둥글게 만드는 기준 좌표를 계산합니다.
    draw_polygon(t, [p_left, p_base, p_right, p_tip], fill_color='#ffffff', line_color='#20232a', width=1.8)  # 4개 정점으로 구성된 흰색 이빨을 그립니다.

def draw_shark_character():  # 상어 캐릭터의 모든 그래픽 레이어를 순서대로 조합해 그리는 메인 함수입니다.
    screen = turtle.Screen()  # 그림을 표시할 Turtle 윈도우 화면 객체를 생성합니다.
    screen.setup(width=760, height=760)  # 정사각형 비율의 760x760 픽셀 창 크기를 설정합니다.
    screen.bgcolor('white')  # 캔버스 배경색을 순백색으로 지정합니다.
    screen.title('Shark Character - Pure Python Standard Library')  # 창 제목을 설정합니다.
    screen.tracer(0)  # 중간 애니메이션을 생략하고 최종 결과를 즉시 렌더링하도록 화면 갱신을 지연시킵니다.

    t = turtle.Turtle()  # 실제 도형을 그릴 거북이 펜 객체를 생성합니다.
    t.hideturtle()  # 완성된 일러스트를 가리지 않도록 거북이 커서를 숨깁니다.
    t.speed(0)  # 내부 그리기 속도를 최고 속도로 설정합니다.

    # --- 1. 꼬리 지느러미 레이어 (가장 뒤쪽) ---
    tail_segments = [  # 홈이 파인 꼬리 지느러미의 3차 베지어 곡선 구간을 정의합니다.
        ((3.8, -3.7), (4.7, -4.1), (5.2, -4.4)),  # 몸통에서 꼬리 줄기 윗부분으로 이어지는 곡선입니다.
        ((5.8, -3.6), (6.8, -3.2), (7.9, -3.4)),  # 꼬리 위쪽 날개 끝으로 뻗어 나가는 곡선입니다.
        ((7.6, -3.6), (7.3, -3.8), (7.1, -3.95)),  # 위쪽 날개 뒷면의 패인 홈 안쪽으로 들어가는 곡선입니다.
        ((7.2, -4.05), (7.35, -4.15), (7.3, -4.25)),  # 패인 홈에서 바깥으로 살짝 튀어나오는 곡선입니다.
        ((6.8, -4.5), (6.3, -4.7), (6.0, -4.95)),  # 꼬리 중앙의 오목한 갈림 부분으로 모이는 곡선입니다.
        ((6.2, -5.5), (6.2, -6.3), (5.85, -6.85)),  # 아래쪽 꼬리 날개 끝으로 내려가는 곡선입니다.
        ((5.2, -6.3), (4.9, -5.7), (4.75, -5.2)),  # 아래쪽 날개 앞면에서 꼬리 줄기로 올라오는 곡선입니다.
        ((4.0, -5.1), (3.2, -4.9), (2.5, -4.7)),  # 꼬리 아래쪽 줄기가 몸통 뒤로 들어가는 곡선입니다.
    ]  # 꼬리 지느러미 베지어 구간 정의를 마칩니다.
    tail_pts = build_bezier_points((2.5, -3.5), tail_segments, steps=18)  # 꼬리 지느러미 전체 정점 리스트를 생성합니다.
    draw_polygon(t, tail_pts, fill_color='#527890', line_color=None)  # 어두운 청회색으로 꼬리 기본 면을 채웁니다.

    tail_lit_segments = [  # 꼬리 윗날개 내부에만 정확히 들어가도록 설계한 밝은 하이라이트 곡선입니다.
        ((5.7, -3.7), (6.7, -3.4), (7.55, -3.52)),  # 윗날개 상단 경계를 따라 뻗어 나가는 밝은 곡선입니다.
        ((7.0, -3.95), (6.3, -4.3), (4.85, -4.55)),  # 윗날개 안쪽을 부드럽게 감싸며 돌아오는 곡선입니다.
    ]  # 꼬리 하이라이트 구간 정의를 마칩니다.
    tail_lit_pts = build_bezier_points((4.85, -4.55), tail_lit_segments, steps=14)  # 꼬리 하이라이트 정점 리스트를 생성합니다.
    draw_polygon(t, tail_lit_pts, fill_color='#73a1bc', line_color=None)  # 밝은 청회색으로 꼬리 광택을 칠합니다.

    for gx in range(56, 77, 2):  # 꼬리 윗날개에 만화풍 망점을 찍기 위해 x 격자를 순회합니다.
        for gy in range(-45, -34, 2):  # 꼬리 윗날개의 y 격자를 순회합니다.
            hx = gx / 10.0  # 정수 격자 값을 실제 모델 x 좌표로 변환합니다.
            hy = gy / 10.0  # 정수 격자 값을 실제 모델 y 좌표로 변환합니다.
            if point_in_polygon(hx, hy, tail_pts):  # 광선 투사법으로 점이 꼬리 내부에 있을 때만 그리도록 필터링합니다.
                t.penup()  # 점 위치로 이동하기 위해 펜을 듭니다.
                t.goto(hx * SCALE, hy * SCALE)  # 해당 망점의 화면 픽셀 좌표로 이동합니다.
                t.dot(3.2, '#99c4da')  # 은은한 하늘색 망점 도트를 찍습니다.
    draw_polygon(t, tail_pts, fill_color=None, line_color='#181b22', width=2.8)  # 하이라이트와 망점 위로 꼬리의 선명한 검은 외곽선을 그립니다.

    # --- 2. 상어 메인 몸통 및 셀 셰이딩 음영 레이어 ---
    body_segments = [  # 상어의 뾰족한 머리, 통통한 몸통, 짧은 두 다리를 이루는 8개의 베지어 구간입니다.
        ((1.1, 7.7), (2.8, 5.2), (3.6, 2.5)),  # 머리 꼭대기에서 오른쪽 어깨로 내려오는 곡선입니다.
        ((4.3, 0.2), (4.5, -2.8), (3.0, -5.0)),  # 오른쪽 옆구리에서 엉덩이로 이어지는 곡선입니다.
        ((2.5, -5.8), (2.3, -7.6), (1.3, -7.7)),  # 오른쪽 바깥 다리에서 발끝으로 내려가는 곡선입니다.
        ((0.5, -7.8), (0.3, -6.4), (0.0, -6.2)),  # 오른쪽 발끝에서 가랑이 중앙으로 올라가는 곡선입니다.
        ((-0.3, -6.4), (-0.5, -7.8), (-1.3, -7.7)),  # 가랑이 중앙에서 왼쪽 발끝으로 내려가는 곡선입니다.
        ((-2.3, -7.6), (-2.5, -5.8), (-3.0, -5.0)),  # 왼쪽 발끝에서 바깥 다리를 타고 올라가는 곡선입니다.
        ((-4.5, -2.8), (-4.3, 0.2), (-3.6, 2.5)),  # 왼쪽 옆구리에서 어깨로 올라가는 곡선입니다.
        ((-2.8, 5.2), (-1.1, 7.7), (0.0, 7.8)),  # 왼쪽 머리 측면을 따라 꼭대기로 닫히는 곡선입니다.
    ]  # 몸통 베지어 구간 정의를 마칩니다.
    body_pts = build_bezier_points((0.0, 7.8), body_segments, steps=24)  # 전체 몸통 외곽 정점 리스트를 생성합니다.
    draw_polygon(t, body_pts, fill_color='#436880', line_color=None)  # 아래쪽 그림자 톤인 어두운 청회색으로 몸통 전체를 먼저 채웁니다.

    lit_body_pts = [(x * 0.88, y * 0.94 + 0.35) for x, y in body_pts]  # 외곽선 안쪽으로 정확히 수축·상향 이동된 밝은 몸통 좌표를 계산합니다.
    draw_polygon(t, lit_body_pts, fill_color='#6f9eb8', line_color=None)  # 메인 피부색인 밝은 청회색을 겹쳐 입체적인 셀 셰이딩을 구현합니다.

    # --- 3. 머리 우상단 하프톤 망점, 이마 광택, 후드 측면 상어 눈 ---
    body_inner_mask = [(x * 0.94, y * 0.97 + 0.1) for x, y in body_pts]  # 망점이 검은 외곽선에 겹치지 않도록 살짝 축소한 내부 판별용 마스크입니다.
    for row in range(13):  # 머리 우상단 망점의 세로 13개 행을 순회합니다.
        for col in range(13):  # 각 행의 가로 13개 열을 순회합니다.
            hy = 4.6 + row * 0.25  # 현재 행의 모델 y 좌표를 계산합니다.
            hx = 0.05 + col * 0.23 + (hy - 6.0) * 0.12  # 미세한 기울기를 적용해 만화풍 망점의 x 좌표를 계산합니다.
            dist = math.hypot(hx - 1.45, hy - 6.85)  # 하이라이트 중심점으로부터의 유클리드 거리를 산출합니다.
            dot_size = max(0.0, (2.3 - dist) * 2.9)  # 중심에 가까울수록 점 지름이 커지도록 선형 감쇠 공식을 적용합니다.
            if dot_size > 1.2 and point_in_polygon(hx, hy, body_inner_mask):  # 점 크기가 유효하고 머리 내부에 속할 때만 렌더링합니다.
                t.penup()  # 다음 망점 좌표로 이동하기 위해 펜을 듭니다.
                t.goto(hx * SCALE, hy * SCALE)  # 모델 좌표를 픽셀 좌표로 변환해 이동합니다.
                t.dot(dot_size, '#9bc9e0')  # 사전 혼합된 밝은 하늘색으로 망점 도트를 찍습니다.

    forehead_glow_pts = ellipse_points(1.05, 5.15, 0.42, 0.68, angle_deg=14, steps=36)  # 이마 우측 물방울형 광택 하이라이트 타원 정점을 생성합니다.
    draw_polygon(t, forehead_glow_pts, fill_color='#9fd4e8', line_color=None)  # 부드러운 하늘색으로 이마 광택을 칠합니다.

    head_right_curve = [(0.0, 7.8)] + sample_cubic_bezier((0.0, 7.8), (1.1, 7.7), (2.8, 5.2), (3.6, 2.5), steps=40)  # 오른쪽 머리 경계 곡선을 40단계로 정밀 샘플링합니다.
    outer_arc = head_right_curve[20:33]  # 상어 눈이 위치할 머리 측면 구간(t=0.50~0.80)을 정확히 슬라이싱합니다.
    p_start, p_end = outer_arc[0], outer_arc[-1]  # 슬라이싱된 외곽 호의 시작점과 끝점을 추출합니다.
    inner_arc = sample_cubic_bezier(p_end, (p_end[0] - 0.58, p_end[1] + 0.35), (p_start[0] - 0.42, p_start[1] - 0.55), p_start, steps=16)  # 머리 안쪽으로 오목하게 감싸는 눈의 안쪽 곡선을 생성합니다.
    right_outer_eye = outer_arc + inner_arc  # 바깥 머리 곡선과 안쪽 곡선을 결합해 넘침 없는 오른쪽 상어 눈을 완성합니다.
    left_outer_eye = [(-x, y) for x, y in right_outer_eye]  # 오른쪽 상어 눈 좌표를 좌우 반전시켜 왼쪽 상어 눈을 생성합니다.
    draw_polygon(t, right_outer_eye, fill_color='#1c1f26', line_color=None)  # 오른쪽 후드 측면의 검은 상어 눈을 채웁니다.
    draw_polygon(t, left_outer_eye, fill_color='#1c1f26', line_color=None)  # 왼쪽 후드 측면의 검은 상어 눈을 채웁니다.

    # --- 4. 흰색 배 영역, 입 아래 그림자, 아랫배 그림자, 몸통 외곽선 ---
    belly_segments = [  # 흰색 상어 배 영역을 정의하는 4개의 베지어 구간입니다.
        ((1.5, 1.5), (2.5, 1.5), (3.15, 1.4)),  # 입 뒤쪽에 가려지는 배의 상단 경계선입니다.
        ((3.55, -0.6), (3.55, -3.2), (2.2, -4.55)),  # 오른쪽 옆구리 안쪽을 따라 내려오는 곡선입니다.
        ((1.1, -5.35), (-1.1, -5.35), (-2.2, -4.55)),  # 아랫배 바닥을 둥글게 감싸는 곡선입니다.
        ((-3.55, -3.2), (-3.55, -0.6), (-3.15, 1.4)),  # 왼쪽 옆구리 안쪽을 따라 올라오는 곡선입니다.
    ]  # 배 영역 베지어 구간 정의를 마칩니다.
    belly_pts = build_bezier_points((-3.15, 1.4), belly_segments, steps=20)  # 배 영역의 닫힌 정점 리스트를 생성합니다.
    draw_polygon(t, belly_pts, fill_color='#f1f4f8', line_color=None)  # 부드러운 미색 흰색으로 상어 배를 채웁니다.

    belly_shadow_segs = [  # 배의 바닥 곡선에 딱 맞게 밀착되는 연회색 아랫배 음영 초승달입니다.
        ((1.1, -5.35), (-1.1, -5.35), (-2.2, -4.55)),  # 원본 배의 바닥 곡선과 동일한 아래쪽 경계입니다.
        ((-1.0, -4.8), (1.0, -4.8), (2.2, -4.55)),  # 안쪽으로 완만하게 돌아오는 그림자 상단 경계입니다.
    ]  # 아랫배 그림자 구간 정의를 마칩니다.
    belly_shadow_pts = build_bezier_points((2.2, -4.55), belly_shadow_segs, steps=18)  # 아랫배 그림자 정점 리스트를 생성합니다.
    draw_polygon(t, belly_shadow_pts, fill_color='#d2dbe5', line_color=None)  # 연회색 아랫배 그림자를 칠합니다.

    mouth_shadow_pts = ellipse_points(0.0, -0.58, 2.25, 0.36, angle_deg=0, steps=36)  # 입 아래로 드리워지는 부드러운 그림자 타원을 생성합니다.
    draw_polygon(t, mouth_shadow_pts, fill_color='#c9d3df', line_color=None)  # 입 아래 그림자를 흰 배 위에 렌더링합니다.

    draw_polygon(t, body_pts, fill_color=None, line_color='#181b22', width=3.2)  # 내부 음영과 눈 위로 선명한 몸통 외곽선을 깔끔하게 마무리합니다.

    # --- 5. 양쪽 지느러미 팔 및 아가미 디테일 ---
    left_arm_outline_segs = [  # 왼쪽 지느러미 팔의 바깥선과 둥근 끝부분을 이루는 베지어 구간입니다.
        ((-4.8, -0.4), (-5.9, -2.0), (-5.7, -3.1)),  # 어깨에서 팔 끝부분으로 내려오는 바깥 곡선입니다.
        ((-5.5, -3.8), (-4.4, -3.6), (-3.6, -1.9)),  # 팔 끝을 돌아 겨드랑이로 올라오는 안쪽 곡선입니다.
    ]  # 왼쪽 팔 외곽선 구간 정의를 마칩니다.
    left_arm_fill_segs = left_arm_outline_segs + [((-3.4, -1.0), (-3.4, 0.0), (-3.6, 0.8))]  # 면 채우기를 위해 어깨 연결선을 덧붙입니다.
    right_arm_outline_segs = mirror_segments_x(left_arm_outline_segs)  # 왼쪽 팔 외곽선을 좌우 반전해 오른쪽 팔 외곽선을 얻습니다.
    right_arm_fill_segs = mirror_segments_x(left_arm_fill_segs)  # 왼쪽 팔 채움 구간을 좌우 반전해 오른쪽 팔 채움 구간을 얻습니다.

    left_arm_pts = build_bezier_points((-3.6, 0.8), left_arm_fill_segs, steps=18)  # 왼쪽 팔 전체 채움 정점을 생성합니다.
    right_arm_pts = build_bezier_points((3.6, 0.8), right_arm_fill_segs, steps=18)  # 오른쪽 팔 전체 채움 정점을 생성합니다.
    draw_polygon(t, left_arm_pts, fill_color='#6f9eb8', line_color=None)  # 왼쪽 팔을 메인 청회색으로 채웁니다.
    draw_polygon(t, right_arm_pts, fill_color='#6f9eb8', line_color=None)  # 오른쪽 팔을 메인 청회색으로 채웁니다.

    left_arm_sh_segs = [  # 왼쪽 팔 아래쪽 테두리 안쪽에 정확히 들어가는 음영 구간입니다.
        ((-5.5, -3.8), (-4.4, -3.6), (-3.6, -1.9)),  # 팔 아래쪽 외곽선과 일치하는 하단 경계입니다.
        ((-4.3, -2.85), (-5.1, -3.15), (-5.7, -3.1)),  # 팔 안쪽으로 돌아오는 그림자 상단 경계입니다.
    ]  # 왼쪽 팔 음영 구간 정의를 마칩니다.
    right_arm_sh_segs = mirror_segments_x(left_arm_sh_segs)  # 왼쪽 팔 음영을 대칭시켜 오른쪽 팔 음영 구간을 얻습니다.
    draw_polygon(t, build_bezier_points((-5.7, -3.1), left_arm_sh_segs, steps=14), fill_color='#4c738c', line_color=None)  # 왼쪽 팔 음영을 칠합니다.
    draw_polygon(t, build_bezier_points((5.7, -3.1), right_arm_sh_segs, steps=14), fill_color='#4c738c', line_color=None)  # 오른쪽 팔 음영을 칠합니다.

    draw_polygon(t, build_bezier_points((-3.6, 0.8), left_arm_outline_segs, steps=18), fill_color=None, line_color='#181b22', width=3.0, closed=False)  # 어깨 연결부를 자연스럽게 열어둔 왼쪽 팔 외곽선을 그립니다.
    draw_polygon(t, build_bezier_points((3.6, 0.8), right_arm_outline_segs, steps=18), fill_color=None, line_color='#181b22', width=3.0, closed=False)  # 어깨 연결부를 자연스럽게 열어둔 오른쪽 팔 외곽선을 그립니다.

    for side in (-1, 1):  # 좌측(-1)과 우측(1) 양쪽 옆구리에 아가미 선을 대칭 배치합니다.
        for offset in (0.0, 0.42, 0.84):  # 3줄의 아가미 선을 수직 간격으로 그리기 위해 오프셋을 순회합니다.
            draw_polygon(t, [(side * 3.45, 2.45 - offset), (side * 3.82, 2.15 - offset)], fill_color=None, line_color='#1e222b', width=1.8, closed=False)  # 짧은 대각선으로 상어 아가미 선을 그립니다.

    # --- 6. 빨간 'SHARK' 스티커 및 42도 회전 텍스트 ---
    sx, sy, s_angle = 1.85, -2.55, 42.0  # 스티커 중심 좌표(x, y)와 반시계 회전 각도(42도)를 설정합니다.
    sw, sh = 2.85, 1.05  # 스티커 직사각형의 가로 너비와 세로 높이를 지정합니다.
    s_rad = math.radians(s_angle)  # 회전 행렬 계산을 위해 각도를 라디안으로 변환합니다.
    cos_s, sin_s = math.cos(s_rad), math.sin(s_rad)  # 회전 코사인·사인 값을 미리 산출합니다.
    local_corners = [(-sw / 2, -sh / 2), (sw / 2, -sh / 2), (sw / 2, sh / 2), (-sw / 2, sh / 2)]  # 회전 전 직사각형의 4개 꼭짓점 로컬 좌표입니다.
    sticker_pts = [(sx + dx * cos_s - dy * sin_s, sy + dx * sin_s + dy * cos_s) for dx, dy in local_corners]  # 2D 회전 변환으로 기울어진 사각형 꼭짓점을 구합니다.
    draw_polygon(t, sticker_pts, fill_color='#ba3c46', line_color='#3c1418', width=2.2)  # 붉은 배경과 어두운 테두리를 가진 스티커 사각형을 그립니다.

    canvas = screen.getcanvas()  # 회전 텍스트를 지원하기 위해 Turtle 하부 Tkinter 캔버스 객체를 가져옵니다.
    canvas.create_text(sx * SCALE, -sy * SCALE, text='SHARK', fill='white', font=('Arial', 16, 'bold'), angle=s_angle)  # y축 부호를 반전한 캔버스 좌표에 42도 회전된 'SHARK' 문구를 배치합니다.

    # --- 7. 상어 입, 붉은 잇몸, 어두운 입 내부 공간 ---
    mx, my = 0.0, 1.55  # 입 아치의 중심 좌표를 설정합니다.
    rx, ry_up, ry_down = 3.18, 2.55, 1.68  # 입의 가로 반지름과 상·하 비대칭 세로 반지름을 지정합니다.
    gum_outer_pts = get_mouth_contour(mx, my, rx, ry_up, ry_down)  # 바깥쪽 짙은 잇몸 윤곽 좌표를 계산합니다.
    gum_inner_pts = get_mouth_contour(mx, my, rx * 0.92, ry_up * 0.91, ry_down * 0.89)  # 안쪽 밝은 잇몸 테두리 좌표를 계산합니다.
    cavity_pts = get_mouth_contour(mx, my, rx * 0.87, ry_up * 0.86, ry_down * 0.84)  # 캐릭터 얼굴이 들어 있는 어두운 입 내부 좌표를 계산합니다.

    draw_polygon(t, gum_outer_pts, fill_color='#962833', line_color='#181b22', width=2.8)  # 짙은 붉은색 바깥 잇몸과 검은 외곽선을 그립니다.
    draw_polygon(t, gum_inner_pts, fill_color='#bd4550', line_color=None)  # 입체감을 주는 밝은 붉은색 안쪽 잇몸을 겹쳐 칠합니다.
    draw_polygon(t, cavity_pts, fill_color='#121317', line_color=None)  # 칠흑 같은 입 안쪽 공간을 채웁니다.

    # --- 8. 입 안의 노란 고리 모양 발광 눈 ---
    for ex in (-1.32, 1.32):  # 왼쪽(-1.32)과 오른쪽(1.32) 두 눈의 x 좌표를 순회합니다.
        ey = 1.62  # 두 눈의 수직 중심 좌표를 지정합니다.
        draw_polygon(t, ellipse_points(ex, ey, 0.88, 0.88, steps=40), fill_color='#312e1b', line_color=None)  # 바깥쪽 은은한 노란빛 번짐(Glow) 1단계 링을 그립니다.
        draw_polygon(t, ellipse_points(ex, ey, 0.80, 0.80, steps=40), fill_color='#5b5427', line_color=None)  # 안쪽 좀 더 밝은 노란빛 번짐 2단계 링을 겹칩니다.
        draw_polygon(t, ellipse_points(ex, ey, 0.73, 0.73, steps=40), fill_color='#ffdf33', line_color=None)  # 선명한 노란색 발광 눈 본체 원을 채웁니다.
        draw_polygon(t, ellipse_points(ex, ey, 0.43, 0.43, steps=36), fill_color='#121317', line_color=None)  # 원 중앙을 배경과 같은 검은색으로 채워 고리 형태를 완성합니다.

    # --- 9. 방사형으로 배치된 12개의 상어 이빨 ---
    teeth_specs = [  # 각 이빨의 (중심 각도, 밑변 절반 각도 너비, 이빨 끝점 비율) 명세 리스트입니다.
        (90, 13, 0.61),  # 정중앙 상단의 가장 큼직한 앞니 명세입니다.
        (56, 12, 0.63),  # 우상단 첫 번째 이빨 명세입니다.
        (124, 12, 0.63),  # 좌상단 첫 번째 이빨 명세입니다.
        (24, 11, 0.65),  # 우상단 두 번째 이빨 명세입니다.
        (156, 11, 0.65),  # 좌상단 두 번째 이빨 명세입니다.
        (0, 10, 0.68),  # 오른쪽 입꼬리 측면 이빨 명세입니다.
        (180, 10, 0.68),  # 왼쪽 입꼬리 측면 이빨 명세입니다.
        (336, 11, 0.66),  # 우하단 측면 이빨 명세입니다.
        (204, 11, 0.66),  # 좌하단 측면 이빨 명세입니다.
        (304, 12, 0.64),  # 우하단 안쪽 이빨 명세입니다.
        (236, 12, 0.64),  # 좌하단 안쪽 이빨 명세입니다.
        (270, 12, 0.63),  # 정중앙 하단 이빨 명세입니다.
    ]  # 12개 이빨 명세 정의를 마칩니다.
    for angle_deg, half_w, tip_s in teeth_specs:  # 정의된 12개의 이빨 명세를 순회하며 하나씩 그립니다.
        draw_tooth(t, mx, my, rx, ry_up, ry_down, angle_deg, half_w, tip_s)  # 헬퍼 함수를 호출해 각 이빨을 잇몸 안쪽에 렌더링합니다.

    screen.update()  # 지연시켜 두었던 모든 벡터 그래픽 버퍼를 화면에 한 번에 출력합니다.
    turtle.done()  # 사용자가 창을 닫을 때까지 이벤트 루프를 유지합니다.

if __name__ == '__main__':  # 이 파일이 메인 스크립트로 직접 실행될 때만 렌더링 함수를 호출합니다.
    draw_shark_character()  # 상어 캐릭터 그리기 메인 함수를 실행합니다.