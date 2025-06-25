import time
from PyQt5.QtCore import QEventLoop
from logger import logger
from config import Config

class Trading:
    """거래 기능 클래스"""
    
    def __init__(self, kiwoom_api):
        self.api = kiwoom_api
        self.order_event_loop = QEventLoop()
        self.tr_event_loop = QEventLoop()
        self.order_result = {}
        self.tr_data = {}
        
        # 이벤트 핸들러 연결
        self._connect_trading_events()
        
        # logger.info("거래 기능 초기화 완료")
    
    def _connect_trading_events(self):
        """거래 관련 이벤트 핸들러 연결"""
        self.api.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)
        self.api.ocx.OnReceiveMsg.connect(self._on_receive_msg)
        self.api.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.api.ocx.OnReceiveTrData.connect(self._on_order_result)
        
        # logger.info("거래 이벤트 핸들러 연결 완료")
    
    def buy_stock(self, code, quantity, price=0, order_type="시장가"):
        """주식 매수 주문"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return False
            
            if Config.is_simulation_mode():
                logger.info(f"시뮬레이션 모드: {code} 매수 {quantity}주")
            
            # 주문 타입 설정
            if order_type == "시장가":
                order_type_code = "03"
            elif order_type == "지정가":
                order_type_code = "00"
            else:
                logger.error(f"지원하지 않는 주문 타입: {order_type}")
                return False
            
            # 주문 실행
            self.order_result = {}
            result = self.api.ocx.SendOrder(
                "매수주문",
                "0101",  # 화면번호
                Config.ACCNO,  # 계좌번호 : 8105608311
                1,  # 주문타입 (1:신규매수)
                code,  # 종목코드
                quantity,  # 주문수량
                price,  # 주문가격
                order_type_code,  # 거래구분
                ""  # 원주문번호
            )
            
            if result == 0:
                logger.info("매수 주문 전송 성공, 결과 대기 중...")
                self.order_event_loop.exec_()
                if self.order_result.get("order_no"):
                    logger.log_trade("매수", code, quantity, price, quantity * price)
                    return True
                else:
                    logger.error("매수 주문이 거부되었습니다.")
                    return False
            else:
                logger.log_error("BUY_ORDER", f"매수 주문 실패 (에러코드: {result})")
                return False
                
        except Exception as e:
            logger.log_error("BUY_STOCK", str(e))
            return False
    
    def sell_stock(self, code, quantity, price=0, order_type="시장가"):
        """주식 매도 주문"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return False
            
            if Config.is_simulation_mode():
                logger.info(f"시뮬레이션 모드: {code} 매도 {quantity}주")
                # return True
            
            # 주문 타입 설정
            if order_type == "시장가":
                order_type_code = "03"
            elif order_type == "지정가":
                order_type_code = "00"
            else:
                logger.error(f"지원하지 않는 주문 타입: {order_type}")
                return False
            
            # 주문 실행
            self.order_result = {}
            result = self.api.ocx.SendOrder(
                "매도주문",
                "0102",  # 화면번호
                Config.ACCNO,  # 계좌번호 : 8105608311
                2,  # 주문타입 (2:신규매도)
                code,  # 종목코드
                quantity,  # 주문수량
                price,  # 주문가격
                order_type_code,  # 거래구분
                ""  # 원주문번호
            )
            
            if result == 0:
                logger.info("매도 주문 전송 성공, 결과 대기 중...")
                self.order_event_loop.exec_()
                if self.order_result.get("order_no"):
                    logger.log_trade("매도", code, quantity, price, quantity * price)
                    return True
                else:
                    logger.error("매도 주문이 거부되었습니다.")
                    return False
            else:
                logger.log_error("SELL_ORDER", f"매도 주문 실패 (에러코드: {result})")
                return False
                
        except Exception as e:
            logger.log_error("SELL_STOCK", str(e))
            return False
    
    def cancel_order(self, order_no, code, quantity):
        """주문 취소"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return False
            
            if Config.is_simulation_mode():
                logger.info(f"시뮬레이션 모드: 주문 취소 {order_no}")
                # return True
            
            # 주문 취소
            self.order_result = {}
            result = self.api.ocx.SendOrder(
                "주문취소",
                "0103",  # 화면번호
                Config.ACCNO,  # 계좌번호 : 8105608311
                3,  # 주문타입 (3:취소주문)
                code,  # 종목코드
                quantity,  # 주문수량
                0,  # 주문가격
                "1",  # 거래구분
                order_no  # 원주문번호
            )
            
            if result == 0:
                logger.info(f"주문 취소 요청 전송: {order_no}, 결과 대기 중...")
                self.order_event_loop.exec_()
                if self.order_result.get("order_no"):
                    logger.info(f"주문 취소 접수: {self.order_result['order_no']}")
                    return True
                else:
                    logger.error("주문 취소가 거부되었습니다.")
                    return False
            else:
                logger.log_error("CANCEL_ORDER", f"주문 취소 실패 (에러코드: {result})")
                return False
                
        except Exception as e:
            logger.log_error("CANCEL_ORDER", str(e))
            return False
    
    def get_stock_price(self, code):
        """현재가 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return 0
            
            price = self.api.get_master_last_price(code)
            try:
                price = float(price.replace(',', ''))  # 혹시 천 단위 콤마가 있을 경우 제거
            except (ValueError, AttributeError):
                price = 0
            
            if price > 0:
                logger.debug(f"{code} 현재가: {price:,}원")
                return price
            else:
                logger.warning(f"{code} 현재가 조회 실패")
                return 0
                
        except Exception as e:
            logger.log_error("GET_STOCK_PRICE", str(e))
            return 0
    
    def get_stock_name(self, code):
        """종목명 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return ""
            
            name = self.api.get_master_code_name(code)
            if name:
                logger.debug(f"{code} 종목명: {name}")
                return name
            else:
                logger.warning(f"{code} 종목명 조회 실패")
                return ""
                
        except Exception as e:
            logger.log_error("GET_STOCK_NAME", str(e))
            return ""
    
    def get_account_info(self):
        """계좌 정보 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return {}
            
            account_info = {
                # "보유계좌개수": self.api.get_login_info("ACCOUNT_CNT"),
                "사용자ID": self.api.get_login_info("USER_ID"),
                "사용자명": self.api.get_login_info("USER_NAME"),
                "서버구분": self.api.get_login_info("GetServerGubun") + " (1 : 모의투자, 나머지 : 실서버)",  # 접속서버 구분을 반환합니다.(1 : 모의투자, 나머지 : 실서버)
                # "키움서버 키보드보안 해지여부": self.api.get_login_info("KEY_BSECGB") + "(0: 정상, 1: 해지)",  # 키보드보안 해지여부를 반환합니다. (0: 정상, 1: 해지)
                # "방화벽": self.api.get_login_info("FIREW_SECGB"),
                # "보유계좌목록": self.api.get_login_info("ACCLIST"),
                # "계좌번호": self.api.get_login_info("ACCNO")
                "계좌번호": Config.ACCNO
            }
            
            # logger.info("계좌 정보 조회 완료")
            return account_info
            
        except Exception as e:
            logger.log_error("GET_ACCOUNT_INFO", str(e))
            return {}

    def get_total_investment(self):
        """총 투자 금액 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return 0

            self.tr_data.pop('opw00018', None)
            self.api.ocx.SetInputValue("계좌번호", Config.ACCNO)
            self.api.ocx.SetInputValue("비밀번호", Config.ACCNO_PASSWORD)
            self.api.ocx.SetInputValue("비밀번호입력매체구분", "00")
            self.api.ocx.SetInputValue("조회구분", "2")
            self.api.ocx.CommRqData("opw00018_req", "opw00018", 0, "2000")
            self.tr_event_loop.exec_()
            return self.tr_data.get('opw00018', {}).get('total_investment', 0)

        except Exception as e:
            logger.log_error("GET_TOTAL_INVESTMENT", str(e))
            return 0

    def get_available_funds(self):
        """주문 가능 금액 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return 0

            self.tr_data.pop('opw00001', None)
            self.api.ocx.SetInputValue("계좌번호", Config.ACCNO)
            self.api.ocx.SetInputValue("비밀번호", Config.ACCNO_PASSWORD)
            self.api.ocx.SetInputValue("비밀번호입력매체구분", "00")
            self.api.ocx.SetInputValue("조회구분", "2")
            self.api.ocx.CommRqData("opw00001_req", "opw00001", 0, "2001")
            self.tr_event_loop.exec_()
            return self.tr_data.get('opw00001', {}).get('available_funds', 0)

        except Exception as e:
            logger.log_error("GET_AVAILABLE_FUNDS", str(e))
            return 0

    def get_holdings(self):
        """보유 종목 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return []

            self.tr_data.pop('opw00018', None)
            self.api.ocx.SetInputValue("계좌번호", Config.ACCNO)
            self.api.ocx.SetInputValue("비밀번호", Config.ACCNO_PASSWORD)
            self.api.ocx.SetInputValue("비밀번호입력매체구분", "00")
            self.api.ocx.SetInputValue("조회구분", "2")     # 조회구분 = 1:합산, 2:개별
            self.api.ocx.CommRqData("opw00018_req", "opw00018", 0, "2002")
            self.tr_event_loop.exec_()
            return self.tr_data.get('opw00018', {}).get('holdings', [])

        except Exception as e:
            logger.log_error("GET_HOLDINGS", str(e))
            return []

    def get_stocks(self):
        """거래량 상위 종목 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return []

            # self.api.ocx.SetInputValue("시장구분", "000")   # (000:전체, 001:코스피, 101:코스닥)
            # self.api.ocx.SetInputValue("정렬구분"	,  "1");   # (1:거래량, 2:거래회전율, 3:거래대금)
            # self.api.ocx.SetInputValue("관리종목포함", "0"); # (0:관리종목 포함, 1:관리종목 미포함, 3:우선주제외, 11:정리매매종목제외, 4:관리종목, 우선주제외, 5:증100제외, 6:증100마나보기, 13:증60만보기, 12:증50만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 14:ETF제외, 15:스팩제외, 16:ETF+ETN제외)
            # self.api.ocx.SetInputValue("신용구분", "0"); # (0:전체조회, 9:신용융자전체, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 8:신용대주)
            # self.api.ocx.SetInputValue("거래량구분", "200"); # (0:전체조회, 5:5천주이상, 10:1만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:500만주이상, 1000:백만주이상)
            # self.api.ocx.SetInputValue("가격구분", "0"); # (0:전체조회, 1:1천원미만, 2:1천원이상, 3:1천원~2천원, 4:2천원~5천원, 5:5천원이상, 6:5천원~1만원, 10:1만원미만, 7:1만원이상, 8:5만원이상, 9:10만원이상)
            # self.api.ocx.SetInputValue("거래대금구분", "100"); # (0:전체조회, 1:1천만원이상, 3:3천만원이상, 4:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상)
            # self.api.ocx.SetInputValue("장운영구분", "0"); # (0:전체조회, 1:장중, 2:장전시간외, 3:장후시간외)
            # self.api.ocx.SetInputValue("거래소구분", "1"); # (1:KRX, 2:NXT, 3:통합, 공백시 KRX 시세조회)

            self.tr_data.pop("OPT10030", None)
            self.api.ocx.SetInputValue("시장구분", "000")
            self.api.ocx.CommRqData("volume_rank_req", "OPT10030", 0, "2003")
            self.tr_event_loop.exec_()
            return self.tr_data.get("OPT10030", {}).get("stocks", [])

        except Exception as e:
            logger.log_error("GET_STOCKS", str(e))
            return []

    def get_upsurge_stocks(self):
        """거래량 급증 상위 종목 조회"""
        try:
            if not self.api.connected:
                logger.error("API가 연결되지 않았습니다.")
                return []

            # TR 요청 횟수 제한(초당 5회)
            # self.api.ocx.SetInputValue("시장구분", "000")   # (000:전체, 001:코스피, 101:코스닥)
            # self.api.ocx.SetInputValue("정렬구분"	,  "1");   # (1:급증량, 2:급증률, 3:급감량, 4:급감률)
            # self.api.ocx.SetInputValue("시간구분", "1"); # (1:분, 2:전일)
            # self.api.ocx.SetInputValue("거래량구분", "200"); # (5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상)
            # self.api.ocx.SetInputValue("시간", "0930"); # 분 입력 (시간구분 분 선택시 입력)   오전 09:30 기준으로 조회하면 전장 대비 급증 종목을 조기에 포착 가능
            # self.api.ocx.SetInputValue("종목조건", "0"); # (0:전체조회, 1:관리종목제외, 3:우선주제외, 11:정리매매종목제외, 4:관리종목,우선주제외, 5:증100제외, 6:증100만보기, 13:증60만보기, 12:증50만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 17:ETN제외, 14:ETF제외, 16:ETF+ETN제외, 15:스팩제외, 20:ETF+ETN+스팩제외)
            # self.api.ocx.SetInputValue("가격구분", "0"); # (0:전체조회, 2:5만원이상, 5:1만원이상, 6:5천원이상, 8:1천원이상, 9:10만원이상)
            # self.api.ocx.SetInputValue("거래소구분", "1"); # (1:KRX, 2:NXT, 3:통합, 공백시 KRX 시세조회)

            self.tr_data.pop("OPT10023", None)
            self.api.ocx.SetInputValue("종목조건", "0")
            self.api.ocx.SetInputValue("시장구분", "000")
            self.api.ocx.CommRqData("upsurge_volume_rank_req", "OPT10023", 0, "2004")
            self.tr_event_loop.exec_()
            return self.tr_data.get("OPT10023", {}).get("upsurge_stocks", [])

        except Exception as e:
            logger.log_error("GET_UPSURGE_STOCKS", str(e))
            return []


    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결잔고 데이터 수신"""
        try:
            if gubun == "0":  # 주문체결통보
                logger.debug("주문체결통보 수신")
            elif gubun == "1":  # 잔고통보
                logger.debug("잔고통보 수신")
            elif gubun == "3":  # 특이신호
                logger.debug("특이신호 수신")
            elif gubun == "4":  # 주문체결통보
                logger.debug("주문체결통보 수신")
            
        except Exception as e:
            logger.log_error("CHEJAN_DATA", str(e))
    
    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        """메시지 수신"""
        try:
            logger.debug(f"거래 메시지: {msg}")
            
            # 주문 관련 메시지 처리
            if "주문" in msg:
                if "성공" in msg:
                    logger.info("주문이 성공적으로 처리되었습니다.")
                elif "실패" in msg:
                    logger.error("주문 처리에 실패했습니다.")
            
        except Exception as e:
            logger.log_error("RECEIVE_MSG", str(e)) 

    def _on_receive_tr_data(self, screen_no, rqname, trcode, recordname, prev_next, data_len, error_code, message, splm_msg):
        """TR 데이터 수신"""
        try:
            if rqname == "opw00018_req":
                total = self.api.ocx.GetCommData(trcode, rqname, 0, "총매입금액")
                try:
                    total = int(total.strip().replace(',', ''))
                except (ValueError, AttributeError):
                    total = 0

                holdings = []
                count = int(self.api.ocx.GetRepeatCnt(trcode, rqname))
                for i in range(count):
                    code = self.api.ocx.GetCommData(trcode, rqname, i, "종목번호").strip()
                    name = self.api.ocx.GetCommData(trcode, rqname, i, "종목명").strip()
                    qty = self.api.ocx.GetCommData(trcode, rqname, i, "보유수량").strip()
                    prcs = self.api.ocx.GetCommData(trcode, rqname, i, "매입가").strip()
                    cur = self.api.ocx.GetCommData(trcode, rqname, i, "현재가").strip()

                    try:
                        qty = int(qty.replace(',', ''))
                    except ValueError:
                        qty = 0
                    try:
                        prcs = int(prcs.replace(',', ''))
                    except ValueError:
                        prcs = 0
                    try:
                        cur = int(cur.replace(',', ''))
                    except ValueError:
                        cur = 0

                    holdings.append({
                        "code": code,
                        "name": name,
                        "quantity": qty,
                        "purchase_price": prcs,
                        "current_price": cur,
                    })

                self.tr_data['opw00018'] = {
                    'total_investment': total,
                    'holdings': holdings
                }

            elif rqname == "opw00001_req":
                available = self.api.ocx.GetCommData(trcode, rqname, 0, "주문가능금액")
                try:
                    available = int(available.strip().replace(',', ''))
                except (ValueError, AttributeError):
                    available = 0
                self.tr_data['opw00001'] = {'available_funds': available}

            elif rqname == "volume_rank_req":
                stocks = []
                count = int(self.api.ocx.GetRepeatCnt(trcode, rqname))
                for i in range(count):
                    code = self.api.ocx.GetCommData(trcode, rqname, i, "종목코드").strip()
                    name = self.api.ocx.GetCommData(trcode, rqname, i, "종목명").strip()
                    volume = self.api.ocx.GetCommData(trcode, rqname, i, "거래량").strip()
                    amount = self.api.ocx.GetCommData(trcode, rqname, i, "거래금액").strip()
                    price = self.api.ocx.GetCommData(trcode, rqname, i, "현재가").strip()

                    try:
                        volume = int(volume.replace(',', ''))
                    except (ValueError, AttributeError):
                        volume = 0
                    try:
                        amount = int(amount.replace(',', ''))
                    except (ValueError, AttributeError):
                        amount = 0
                    try:
                        price = int(price.replace(',', ''))
                    except (ValueError, AttributeError):
                        price = 0

                    stocks.append({
                        "code": code,
                        "name": name,
                        "price": price,
                        "vol": volume,
                        "amount": amount,
                    })

                self.tr_data["OPT10030"] = {"stocks": stocks[:20]}

            elif rqname == "upsurge_volume_rank_req":
                upsurge_stocks = []
                count = int(self.api.ocx.GetRepeatCnt(trcode, rqname))
                for i in range(count):
                    code = self.api.ocx.GetCommData(trcode, rqname, i, "종목코드").strip()
                    name = self.api.ocx.GetCommData(trcode, rqname, i, "종목명").strip()
                    pre_volume = self.api.ocx.GetCommData(trcode, rqname, i, "이전거래량").strip()
                    cur_volume = self.api.ocx.GetCommData(trcode, rqname, i, "현재거래량").strip()
                    fluctuation_rate = self.api.ocx.GetCommData(trcode, rqname, i, "등락률").strip()
                    price = self.api.ocx.GetCommData(trcode, rqname, i, "현재가").strip()

                    try:
                        pre_volume = int(pre_volume.replace(',', ''))
                    except (ValueError, AttributeError):
                        pre_volume = 0
                    try:
                        cur_volume = int(cur_volume.replace(',', ''))
                    except (ValueError, AttributeError):
                        cur_volume = 0
                    try:
                        price = int(price.replace(',', ''))
                    except (ValueError, AttributeError):
                        price = 0

                    upsurge_stocks.append({
                        "code": code,
                        "name": name,
                        "price": price,
                        "pre_vol": pre_volume,
                        "cur_vol": cur_volume,
                        "fluctuation_rate": fluctuation_rate,
                    })

                self.tr_data["OPT10023"] = {"upsurge_stocks": upsurge_stocks[:20]}

        except Exception as e:
            logger.log_error("RECEIVE_TR_DATA", str(e))
        finally:
            self.tr_event_loop.exit()

    def _on_order_result(self, screen_no, rqname, trcode, recordname, prev_next, data_len, error_code, message, splm_msg):
        """주문 처리 결과 수신"""
        try:
            if rqname not in ("매수주문", "매도주문", "주문취소"):
                return

            order_no = self.api.ocx.GetCommData(trcode, rqname, 0, "주문번호").strip()
            state = self.api.ocx.GetCommData(trcode, rqname, 0, "주문상태").strip()
            qty = self.api.ocx.GetCommData(trcode, rqname, 0, "주문수량").strip()
            price = self.api.ocx.GetCommData(trcode, rqname, 0, "주문가격").strip()

            try:
                qty = int(qty.replace(',', ''))
            except (ValueError, AttributeError):
                qty = 0
            try:
                price = int(price.replace(',', ''))
            except (ValueError, AttributeError):
                price = 0

            self.order_result = {
                'order_no': order_no,
                'state': state,
                'quantity': qty,
                'price': price
            }

            if order_no:
                logger.info(f"주문 접수 성공: {order_no} ({state})")
            else:
                logger.error(f"주문 접수 실패: {message}")

        except Exception as e:
            logger.log_error("ORDER_RESULT", str(e))
        finally:
            self.order_event_loop.exit()